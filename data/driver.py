import importlib
import importlib.util
import json
import time
from pathlib import Path
from textwrap import dedent
from types import ModuleType

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import HttpUrl
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from data.scraped_camp import ScrapedCamp
from data.site_list import HTTP_SITES

OPENAI_MODEL = "gpt-4o"
CHAT_CLIENT = ChatOpenAI(model=OPENAI_MODEL)


def download_rendered_html(
    driver: webdriver.Chrome, url: HttpUrl, wait_selector=None, wait_time=10
) -> str:
    try:
        print(f"Loading {url}")
        driver.get(str(url))

        # Wait for specific element if provided (recommended)
        if wait_selector:
            WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
            )
        else:
            # Otherwise, wait a fixed time
            time.sleep(wait_time)

        # Get the full rendered HTML
        html = driver.page_source
        return html

    except Exception as e:
        driver.quit()
        raise e


def create_explorer_script(
    chat_client: ChatOpenAI, driver: webdriver.Chrome, html_page: str
) -> str:
    """Generates script that takes an HTML page and walks through the pages and collects
    all the leaf pages, returns it a string.
    """

    _INSTRUCTIONS: str = dedent("""
    Given the following webpage, write selenium code that collects the urls of all
    landing pages that can show up in the search functionality, including pagination. We
    use an initialized  `driver` of type `webdriver.Chrome`. The signature of the
    generated python code should be, returning a list of landing page urls:
                        
    ```
    def explore_page(driver: webriver.Chrome, url: str) -> list[str]
    ```
    
    Remember the following: 
    - don't click out of the website, just collect the landing page links
    - pagination might be infinite scroll or you might need click on a button to load 
      more 
    - you can only interact with visible elements, make sure you scroll to them (eg click)
    - you might need to enter queries into the search box, or change filters
    - make sure you pretend to be a human, so add human-like behavior when exploring
      the website
    - make sure to import everything you use
    
    ONLY RETURN THE PYTHON CODE!!! No markdown, no explanations.
    
    """)

    response: BaseMessage = chat_client.invoke(
        [SystemMessage(_INSTRUCTIONS), HumanMessage(html_page)]
    )

    return str(response.content)


def create_extractor_script(
    chat_client: ChatOpenAI, driver: webdriver.Chrome, html_pages: list[str]
) -> str:
    schema_definiton = (Path(__file__).parent / "scraped_camp.py").read_text()
    _INSTRUCTIONS: str = dedent(f"""
    Given the following webpages, write selenium code that extracts all available 
    information for the camp or camps listed on the page. The structured data should
    follow the following schema:
                                
    ```
    {schema_definiton}
    ```

    The signature of the generated python code should be, returning a list of camps:
    ```
    from data.scraped_camp import ScrapedCamp
    from selenium import webdriver

    def extract_camps(driver: webriver.Chrome, url: str) -> list[ScrapedCamp]
    ```
    
    Remember the following: 
    - you might need to convert dates to YYYY-MM-DD format
    - make date parsing very robust
    - you might need to map back the age to the swiss system (4-5 = kindergarten, 6 =
      1st grade, 7 = 2nd grade, ...) to get the age_from and age_to
    - make sure to import everything you use
    - if you cannot process a camp, just skip it, but do not crash
    - break the code into functions if needed

    
    ONLY RETURN THE PYTHON CODE!!! No markdown, no explanations, just pure python. Don't
    add markdown to indicate the code block, just return the code.
    
    """)

    response: BaseMessage = chat_client.invoke(
        [SystemMessage(_INSTRUCTIONS)]
        + [HumanMessage(html_page) for html_page in html_pages]
    )

    return str(response.content)


def import_from_dotted_dir(
    directory: Path, module_name: str, file_name: str
) -> ModuleType:
    """
    Imports a module from a directory with a dot in its name.

    Args:
        directory_name (str): The name of the directory (e.g., "my.special.dir").
        module_name (str): The name to assign to the imported module.
        file_name (str): The name of the Python file (e.g., "my_module.py").

    Returns:
        The imported module object, or None if an error occurred.
    """

    file_path = directory / file_name
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    assert spec
    assert spec.loader
    module = importlib.util.module_from_spec(spec)
    assert module
    spec.loader.exec_module(module)
    return module


def load_and_execute_explorer(
    driver: webdriver.Chrome, directory: Path, start_url: HttpUrl
):
    explorer = import_from_dotted_dir(
        directory, module_name="explorer", file_name="explorer.py"
    )
    explorer_function = getattr(explorer, "explore_page")
    landing_pages: list[str] = explorer_function(driver, str(start_url))
    (directory / "landing_pages.lst").write_text("\n".join(landing_pages))


def load_and_execute_extractor(driver: webdriver.Chrome, directory: Path):
    extractor = import_from_dotted_dir(
        directory, module_name="extractor", file_name="extractor.py"
    )
    extractor_function = getattr(extractor, "extract_camps")
    urls = (directory / "landing_pages.lst").read_text().splitlines()
    camps: list[ScrapedCamp] = []
    for url in urls:
        print(f"Processing {url}")
        camps_on_page: list[ScrapedCamp] = extractor_function(driver, url)
        for camp in camps_on_page:
            if camp not in camps:
                camps.append(camp)

    # Save the camps to a file
    camps_json = [camp.model_dump() for camp in camps]
    with open(directory / "camps.json", "w") as f:
        json.dump(camps_json, f, indent=2)


def process_one_site(driver: webdriver.Chrome, url: HttpUrl, sitename: str):
    print(f"Processing {sitename}")
    directory = Path(f"data/sites/{sitename}/")
    directory.mkdir(exist_ok=True, parents=True)
    (directory / "__init__.py").touch()

    print("Generating explorer script")
    # html = download_rendered_html(driver, url)
    #     script = create_explorer_script(
    #         chat_client=CHAT_CLIENT, driver=driver, html_page=html
    #     )
    #
    #     (directory / "explorer.py").write_text(script)
    load_and_execute_explorer(driver, directory, url)

    # Extraction.
    print("Generating extractor script")
    example_pages = [
        download_rendered_html(driver, HttpUrl(url))
        for url in (directory / "landing_pages.lst").read_text().splitlines()[:2]
    ]
    extractor_script: str = create_extractor_script(
        chat_client=CHAT_CLIENT,
        driver=driver,
        html_pages=example_pages,
    )
    (directory / "extractor.py").write_text(extractor_script)
    load_and_execute_extractor(driver, directory)


def main():
    # Set up headless Chrome
    options = Options()
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    # Initialize the WebDriver
    driver = webdriver.Chrome(options=options)

    for sitename, url in HTTP_SITES.items():
        process_one_site(driver, url, sitename)

    driver.quit()


if __name__ == "__main__":
    main()

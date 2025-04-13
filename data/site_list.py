from pydantic import HttpUrl

API_SITES: dict[HttpUrl, str] = {
    HttpUrl("https://www.jugendsportcamps.ch/"): "jugendsportcamps.ch",
}


HTTP_SITES: dict[str, HttpUrl] = {
    "zsf.ch": HttpUrl("https://www.zsf.ch/ferienprogramm/"),
}

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from urllib.request import urlopen
from bs4 import BeautifulSoup
import chardet

app = FastAPI()

class LdvItem(BaseModel):
    pr_id: int
    ldv: str

class LdvList(BaseModel):
    items: list[LdvItem]

@app.get("/")
def hello():
    return {"Hello": "World"}

@app.get("/ldv-summary")
def ldv_list(ldv_list: LdvList):
    ok = 0
    ko = 0
    waiting = 0
    not_found = 0
    retval = {}

    for item in ldv_list.items:
        status = ldv_status(item.ldv)
        if status == "CONSEGNATA":
            ok += 1
        elif status == "NON CONSEGNATA":
            ko += 1
        elif status == "NON TROVATA":
            not_found += 1
        else:
            waiting += 1    
    retval.update({"CONSEGNATE": ok, "NON CONSEGNATE": ko, "IN TRANSITO": waiting, "NON TROVATE": not_found})

    return retval

@app.post("/ldv-list")
def ldv_list(ldv_list: LdvList):
    retval = {
        "items": [

        ]
    }

    for item in ldv_list.items:
        status = ldv_status(item.ldv)
        retval["items"].append({"pr_id": f"{item.pr_id}", "status": f"{status}"})
        #retval["items"].update({f"{item.pr_id}": f"{status}"})

    return retval

@app.get("/ldv-status")
def ldv_status(ldv: str = ""):
    BASE_URL = "https://vas.brt.it/vas/sped_det_show.hsm?Nspediz="
    LDV_URL = "&referer=sped_rifmittente_lista.hsm&ReqID=244073909&pagina=3&dataSpedizione=09%2F09%2F2024"
    URL = BASE_URL + ldv + LDV_URL

    try:
        page = urlopen(URL)
        raw_data = page.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        html = raw_data.decode(encoding)
    except:
        return "NON TROVATA"

    soup = BeautifulSoup(html, "html.parser")
    status_table = soup.find("table", class_="table_stato_dati")
    if status_table is None:
        return "NON TROVATA"
    
    status_rows = status_table.findChildren(['tr'])
    status = status_rows[1].findChildren(['td'])[3].decode_contents().replace('\xa0', ' ')

    return status
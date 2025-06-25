import re
from bs4 import BeautifulSoup

def get_lni_info_from_html(list_html: str, detail_htmls: list[str]) -> list[dict]:
    contractors = []
    print("🔧 Parsing LNI Detail Pages")
    for idx, detail_html in enumerate(detail_htmls):
        soup = BeautifulSoup(detail_html, "html.parser")
        info = {}

        contractor_name_tag = soup.select_one("div.hdrText")
        contractor_name = contractor_name_tag.get_text(strip=True) if contractor_name_tag else f"Contractor #{idx + 1}"
        print(f"📄 {contractor_name} Detail Page:")

        for table in soup.select("table"):
            for row in table.select("tr"):
                cols = row.find_all("td")
                if len(cols) >= 2:
                    label = cols[0].get_text(strip=True).rstrip(":")
                    value = cols[1].get_text(strip=True)
                    if "Registration #" in label:
                        info["Registration Number"] = value
                    elif "License Suspended" in label:
                        info["License Suspended"] = value
                    elif "Insurance Company" in label:
                        info["Insurance Company"] = value
                    elif "Insurance Amount" in label:
                        info["Insurance Amount"] = value

        bonds = []
        for h4 in soup.find_all("h4", string=re.compile("Bond Information", re.I)):
            bond_table = h4.find_next("table")
            if bond_table:
                for row in bond_table.select("tr")[1:]:
                    cols = [td.get_text(strip=True) for td in row.select("td")]
                    if len(cols) >= 3:
                        bonds.append({
                            "Bonding Company": cols[0],
                            "Bond Number": cols[1],
                            "Amount": cols[2],
                        })
        if bonds:
            info["Bonds"] = bonds

        lawsuits = []
        for h4 in soup.find_all("h4", string=re.compile("Lawsuits", re.I)):
            lawsuit_table = h4.find_next("table")
            if lawsuit_table:
                for row in lawsuit_table.select("tr")[1:]:
                    cols = [td.get_text(strip=True) for td in row.select("td")]
                    if len(cols) >= 4:
                        lawsuits.append({
                            "Case Number": cols[0],
                            "County": cols[1],
                            "Parties": cols[2],
                            "Status": cols[3],
                        })
        if lawsuits:
            info["Lawsuits"] = lawsuits

        if info:
            contractors.append(info)
            print(f"✅ Parsed: {contractor_name} → {list(info.keys())}")
        else:
            print("⚠️  No data extracted.")

    return contractors
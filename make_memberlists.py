import datetime
import os

import pandas as pd
from tqdm import tqdm

import utils

model_name = "gpt-5-nano"


def make_member_list(lablist_csv):
    df = pd.read_csv(lablist_csv)
    print(df.info())

    table = []
    for i, row in tqdm(df.iterrows()):
        grad_name, faculty_name, field_name, lab_name, lab_url = (
            row["大学院"],
            row["研究科"],
            row["専攻"],
            row["研究室"],
            row["URL"],
        )

        if pd.isna(lab_url):
            continue

        field_domain = utils.get_domain(lab_url)

        with open("prompts/04_member.txt") as f:
            query = f.read()
            query = query.format(
                grad=grad_name,
                faculty=faculty_name,
                field=field_name,
                lab=lab_name,
                url=lab_url,
            )

        resp_member = utils.search_website(query, field_domain, model_name=model_name)
        if not resp_member or "Not Found" in resp_member:
            print(
                f"Member not found: {grad_name} {faculty_name} {field_name} {lab_name} ({field_domain})"
            )
            continue

        members = resp_member.split("\n")
        if len(members) != 3:
            print(
                f"CSV Parse Error: {grad_name} {faculty_name} {field_name} {lab_name} {resp_member}"
            )
            continue

        member_name, member_role, year = (
            members[0].strip(),
            members[1].strip(),
            members[2].strip(),
        )


if __name__ == "__main__":
    lablist = f"output/{datetime.date.today()}/lablist.csv"
    if not os.path.exists(lablist):
        print(
            f"Lab list not found: {lablist}. Please make sure the directory date is today."
        )
        exit(1)

    make_member_list(lablist)

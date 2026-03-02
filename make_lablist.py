import datetime
import os
from collections import deque

import pandas as pd

import utils

grads = [
    # Tier 1
    ("東京大学大学院", "u-tokyo.ac.jp/ja/schools-orgs"),
    ("京都大学大学院", "kyoto-u.ac.jp/ja/faculties-and-graduate"),
    # # Tier 2
    # ("北海道大学大学院", "grad.hokudai.ac.jp"),
    # ("東北大学大学院", "tohoku.ac.jp"),
    # ("名古屋大学大学院", "nagoya-u.ac.jp"),
    # ("大阪大学大学院", "osaka-u.ac.jp"),
    # ("九州大学大学院", "kyushu-u.ac.jp"),
    # ("東京科学大学大学院", "isct.ac.jp"),
]

costs = {
    # https://developers.openai.com/api/docs/pricing
    "gpt-5-nano": (0.05, 0.4),
    "gpt-5-mini": (0.25, 2.0),
    "gpt-5": (1.25, 10.0),
}


def fullname(name, parent1, parent2):
    pass


def make_lab_list(output_dir: str, model_name: str):
    max_depth = 3
    lablist_dir = f"{output_dir}/lablist"
    if not os.path.exists(lablist_dir):
        os.makedirs(lablist_dir)

    input_tokens, output_tokens = 0, 0

    for grad_name, grad_url in grads:
        print(f"Searching {grad_name} on {grad_url} ...")

        # Initialize tables for each depth
        tables = {i: [] for i in range(1, max_depth + 1)}

        with open("prompts/01_faculty.md") as f:
            query = f.read()
            query = query.format(grad=grad_name, url=grad_url)

        resp_faculty = utils.search_website(query, grad_url, model_name=model_name)
        if resp_faculty is None:
            continue

        input_tokens += resp_faculty.usage.input_tokens
        output_tokens += resp_faculty.usage.output_tokens

        resp_faculty = resp_faculty.output_text.strip()
        if "Not Found" in resp_faculty:
            print(f"Faculty Not Found: {grad_name} ({grad_url})")
            continue

        # Parse resp_faculty (CSV format) into deque of tuples: (name, url, depth, parent1, parent2)
        faculty_lines = [line.strip() for line in resp_faculty.split("\n")]
        faculty_list = []
        for line in faculty_lines:
            if line:
                parts = line.split(",")
                if len(parts) == 2:
                    faculty_name, url = parts[0].strip(), parts[1].strip()
                    faculty_list.append((faculty_name, url, 1, None, None))

        dq = deque(faculty_list)

        while dq:
            faculty_name, url, depth, parent1, parent2 = dq.popleft()

            with open("prompts/02_intermediate.md") as f:
                query = f.read()
                # TODO: Use Fullname
                query = query.format(faculty=faculty_name, url=url)

            resp = utils.search_website(query, url, model_name=model_name)
            if resp is None:
                continue

            input_tokens += resp.usage.input_tokens
            output_tokens += resp.usage.output_tokens

            resp_text = resp.output_text.strip()

            if resp_text.startswith("0"):
                # Neither member list nor laboratory/field list was found
                continue

            elif resp_text.startswith("1"):
                # Members list found - add to table as leaf node
                if depth == 1:
                    tables[1].append([grad_name, faculty_name, "", "", url])
                elif depth == 2:
                    tables[2].append([grad_name, parent1, faculty_name, "", url])
                elif depth == 3:
                    tables[3].append([grad_name, parent1, parent2, faculty_name, url])
                continue

            elif resp_text.startswith("2"):
                # Laboratory/Field list exists - parse CSV lines
                lines = resp_text.split("\n")
                csv_lines = lines[1:]

                if depth < max_depth:
                    # Expand queue with new entries
                    for line in csv_lines:
                        line = line.strip()
                        if line:
                            parts = line.split(",")
                            if len(parts) == 2:
                                new_name, new_url = parts[0].strip(), parts[1].strip()
                                if depth == 1:
                                    dq.append(
                                        (new_name, new_url, 2, faculty_name, None)
                                    )
                                elif depth == 2:
                                    dq.append(
                                        (new_name, new_url, 3, parent1, faculty_name)
                                    )
                else:
                    # depth == max_depth: treat as leaf node - add all to table
                    for line in csv_lines:
                        line = line.strip()
                        if line:
                            parts = line.split(",")
                            if len(parts) == 2:
                                new_name, new_url = parts[0].strip(), parts[1].strip()
                                tables[depth].append(
                                    [grad_name, parent1, parent2, new_name, new_url]
                                )

        # Output CSV files for each depth
        depth_columns = {
            1: ["Level 0: 大学院", "Level 1", "Level 2", "Level 3", "URL"],
            2: ["Level 0: 大学院", "Level 1", "Level 2", "Level 3", "URL"],
            3: ["Level 0: 大学院", "Level 1", "Level 2", "Level 3", "URL"],
        }
        
        for depth in range(1, max_depth + 1):
            if tables[depth]:
                output = f"{lablist_dir}/{grad_name}_depth{depth}.csv"
                df = pd.DataFrame(tables[depth], columns=depth_columns[depth])
                df.to_csv(output, index=False)

    print(f"Total input tokens: {input_tokens}")
    print(f"Total output tokens: {output_tokens}")
    cost = costs.get(model_name)
    if cost:
        price_in, price_out = cost
        print(
            f"Total cost ({model_name}): ${(input_tokens * price_in + output_tokens * price_out) / 1000000:.4f}"
        )
    else:
        print("Model cost undefined.")


if __name__ == "__main__":
    model_name = "gpt-5-nano"

    output_dir = f"output/{datetime.date.today()}"
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    make_lab_list(output_dir, model_name)

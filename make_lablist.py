import datetime
import os
from collections import deque

import pandas as pd

import utils

NUM_INTERMEDIATE_LAYES = 3

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


class Node:
    def __init__(self, depth, grad, node1, node2, node3, name, url):
        self._depth = depth
        self.root = grad
        self.children = [node1, node2, node3]
        self.current = name
        self._url = url

    def depth(self):
        return self._depth

    def url(self):
        return self._url

    def row(self):
        return (
            self.depth(),
            self.root,
            *self.children,
            self.current,
            self.url(),
        )

    def child(self, leaf, url):
        children = [c for c in self.children if c]
        children.append(self.current)
        children += [None] * (NUM_INTERMEDIATE_LAYES - len(children))

        return Node(
            self.depth() + 1,
            self.root,
            *children,
            leaf,
            url,
        )

    def fullname(self):
        parts = [self.root, *self.children, self.current]
        return " ".join(str(p) for p in parts if p)


def make_lab_list(output_dir: str, model_name: str):
    lablist_dir = f"{output_dir}/lablist"
    os.makedirs(lablist_dir, exist_ok=True)

    for grad_name, grad_url in grads:
        print(f"Searching {grad_name} on {grad_url} ...")
        visited = {grad_url}
        input_tokens, output_tokens = 0, 0

        # Init tables
        data, intermediate = [], []

        with open("prompts/01_faculty.md") as f:
            query = f.read()
            query = query.format(grad=grad_name, url=grad_url)

        resp = utils.search_website(query, grad_url, model_name=model_name)
        if resp is None:
            continue

        input_tokens += resp.usage.input_tokens
        output_tokens += resp.usage.output_tokens

        if "Not Found" in resp:
            print(f"  Faculty Not Found: {grad_name} ({grad_url})")
            continue

        dq = deque()
        faculty_lines = resp.output_text.split("\n")
        for line in faculty_lines:
            if line:
                parts = line.split(",")
                if len(parts) == 2:
                    name, url = parts[0].strip(), parts[1].strip()
                    dq.append(Node(0, grad_name, None, None, None, name, url))

        while dq:
            node: Node = dq.popleft()
            url = node.url()
            if url is None or url in visited:
                continue

            with open("prompts/02_intermediate.md") as f:
                query = f.read()
                query = query.format(faculty=node.fullname(), url=url)

            resp = utils.search_website(query, url, model_name=model_name)
            visited.add(url)

            if resp is None:
                continue

            input_tokens += resp.usage.input_tokens
            output_tokens += resp.usage.output_tokens

            resp_text = resp.output_text.strip()

            if resp_text.startswith("0"):
                # No lists exist for field, laboratory, or members
                pass

            elif resp_text.startswith("1"):
                # Members list exists - add node to table
                data.append(node.row()[1:])
                if len(data) % 100 == 0:
                    print(f"    {len(data)} laboratories found.")

            else:
                # Subfield or laboratory list exists
                intermediate.append(node.row()[1:])

                # Parse CSV lines
                lines = resp_text.split("\n")
                if len(lines) < 2:
                    continue
                for line in lines[1:]:
                    line = line.strip()
                    if line:
                        parts = line.split(",")
                        if len(parts) == 2:
                            new_name, new_url = parts[0].strip(), parts[1].strip()
                            if new_url == "NA":
                                new_url = None

                            new_node: Node = node.child(new_name, new_url)

                            if resp_text.startswith("2"):
                                # Subfield
                                if node.depth() < NUM_INTERMEDIATE_LAYES:
                                    dq.append(new_node)
                                else:
                                    intermediate.append(new_node.row()[1:])

                            elif resp_text.startswith("3"):
                                # Laboratory
                                data.append(new_node.row()[1:])
                                if len(data) % 100 == 0:
                                    print(f"    {len(data)} laboratories found.")

        # Output CSV files for each depth
        cols = ["大学院", "研究科", "分野1", "分野2", "研究室", "URL"]

        if data:
            output = f"{lablist_dir}/{grad_name}.csv"
            df = pd.DataFrame(data, columns=cols)
            df.to_csv(output, index=False)
        if intermediate:
            output = f"{lablist_dir}/{grad_name}_intermediate.csv"
            df = pd.DataFrame(intermediate, columns=cols)
            df.to_csv(output, index=False)

        print(f"  Total input  tokens: {input_tokens}")
        print(f"  Total output tokens: {output_tokens}")
        cost = costs.get(model_name)
        if cost:
            price_in, price_out = cost
            print(
                f"  Total cost ({model_name}): ${(input_tokens * price_in + output_tokens * price_out) / 1000000:.4f}"
            )
        else:
            print("  Model cost undefined.")


if __name__ == "__main__":
    model_name = "gpt-5-nano"

    output_dir = f"output/{datetime.date.today()}"
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    make_lab_list(output_dir, model_name)

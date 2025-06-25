def wait_for_continue(prompt="Press ENTER to continue, or ';' to skip.") -> bool:
    resp = input(prompt)
    return resp.strip() != ";"

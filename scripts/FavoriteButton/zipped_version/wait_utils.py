def wait_for_continue(prompt="Press ENTER to continue, or ';' to skip."):
    resp = input(prompt)
    return resp.strip() != ";"
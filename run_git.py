import subprocess

def run_git(files, message, branch="main"):
    # Stage changes
    subprocess.run(["git", "add", files], check=True)
    print("---------succesfully staged------")

    # Commit changes
    subprocess.run(["git", "commit", "-m", message], check=True)
    print("---------succesfully commited------")

    # Push to remote
    subprocess.run(["git", "push", "origin", branch], check=True)
    print("---------succesfully pushed------")

# Example usage
run_git(".", " put and filtering operations", "main")



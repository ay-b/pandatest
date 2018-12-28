import os
import sys
import time
import shutil
import requests
import json


def check_deploy_folder_exist(stuff_path, clean=0):
    if os.path.isdir(stuff_path) and clean == 1:
        print("INFO:Deploy folder already exists. Deleting...")
        remove_deploy_folder(stuff_path)
    elif os.path.isdir(stuff_path) and clean != 1:
        print("INFO:Deployment folder in place")
    else:
        print("INFO:No deployment folder detected.")


def remove_deploy_folder(stuff_path):
    print("INFO:Removing folder: " + stuff_path)
    shutil.rmtree(stuff_path)
    if os.path.isdir(stuff_path):
        print("ERROR: Failed. Exiting.")
        exit(1)


def create_deploy_folder(stuff_path):
    clean = 1
    check_deploy_folder_exist(stuff_path, clean)
    os.mkdir(stuff_path, 0o755);
    check_deploy_folder_exist(stuff_path)


def get_git_repo(repo, stuff_path):
    cmd = "git clone " + repo + " " + stuff_path
    check_cmd_exit_code(cmd)


def create_images_folder(stuff_path):
    print("INFO:Creating images folder")
    os.mkdir(stuff_path + "/public/images")
    if os.path.isdir(stuff_path + "/public/images"):
        print("INFO:Images folder in place")
    else:
        print("ERROR: Error creating images folder")
        exit(1)


def check_content_type(content_url):
    print("INFO:Checking content type")
    res = requests.get(content_url)
    content_type = res.headers['content-type']
    if content_type == "application/x-gzip":
        print("INFO:Found zipped content. Proceeding.")
    else:
        print("ERROR: Unexpected thing at URL.")
        exit(1)
    return content_type


def unzip_content(content_folder, filename):
    cmd = "tar -xzvf " + content_folder + "/" + filename + " -C " + content_folder
    check_cmd_exit_code(cmd)
    cmd = "rm " + content_folder + "/" + filename
    os.system(cmd)


def download_content(content_url, content_folder, filename):
    print("INFO:Downloading content bundle.")
    check_content_type(content_url)
    bundle = requests.get(content_url, allow_redirects=True)
    with open(content_folder + "/" + filename, "wb") as r:
        r.write(bundle.content)
    print("INFO:Finished downloading.")
    return filename


def build_container(stuff_path, name, tag, dockerfile_path, assets_path):
    print("INFO:Building " + name + ":" + tag + " container")
    cmd = "docker build -t " + name + ":" + tag + " -f " +  stuff_path + dockerfile_path + " " + stuff_path + assets_path
    check_cmd_exit_code(cmd)
    cmd = "docker images | grep " + name
    os.system(cmd)


def check_cmd_exit_code(cmd):
    exit_code = os.system(cmd)
    if exit_code == 0:
        print("INFO: Command completed succesfully.")
    else:
        print("ERROR: Command execution failed. Exiting.")
        exit(1)


def health_check(check_url):
    chk_counter: int = 0
    checking = True
    while checking:
        chk_counter += 1
        try:
            response = json.dumps(requests.get(check_url).text)
            if 'false' in response:
                print("\nERROR: CRITICAL: Stack is unhealthy")
                print("INFO: " + response)
                checking = False
            else:
                sys.stdout.write("\rOK: Cycle #" + str(chk_counter))
                time.sleep(1)
        except:
            print("\nERROR: CRITICAL: Stack is unhealthy. Web-server is down")
            exit(1)


def main():
    stuff_path = "./temp_deploy"
    repo = "https://github.com/bigpandaio/ops-exercise"
    content_url = "https://s3.eu-central-1.amazonaws.com/devops-exercise/pandapics.tar.gz"
    content_folder = stuff_path + "/public/images"
    filename = content_url.rsplit('/', 1)[1]
    check_url = "http://localhost:3030/health"

    # Downloading/preparing stuff
    create_deploy_folder(stuff_path)
    get_git_repo(repo, stuff_path)
    create_images_folder(stuff_path)
    download_content(content_url, content_folder, filename)
    unzip_content(content_folder,filename)

    # Working with docker
    print("INFO:Building docker containers")
    build_container(stuff_path, "mongo", "panda", "/db/Dockerfile", "/db/")
    build_container(stuff_path, "node", "panda", "/Dockerfile ", " ")
    print("INFO:Launching the stack with docker-compose.")
    cmd = "docker-compose up -d"
    check_cmd_exit_code(cmd)

    # Health-checks
    print("Now starting a health-check in 10 seconds")
    time.sleep(10)
    health_check(check_url)


if __name__ == "__main__":
    main()

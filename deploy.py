import os
import shutil
import requests


def check_deploy_folder_exist(stuff_path, clean=0):
    if os.path.isdir(stuff_path) and clean == 1:
        print("Deploy folder already exists. Deleting...")
        remove_deploy_folder(stuff_path)
    elif os.path.isdir(stuff_path) and clean != 1:
        print("Deployment folder in place")
    else:
        print("No deployment folder detected.")


def remove_deploy_folder(stuff_path):
    print("Removing folder: " + stuff_path)
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
    exit_code = os.system(cmd)
    if exit_code == 0:
        print("Sources obtained")
    else:
        print("ERROR: Failed to obtain sources. Exiting.")
        exit(1)


def create_images_folder(stuff_path):
    print("Creating images folder")
    os.mkdir(stuff_path + "/public/images")
    if os.path.isdir(stuff_path + "/public/images"):
        print("Images folder in place")
    else:
        print("ERROR: Error creating images folder")
        exit(1)



def check_content_type(content_url, content_type):
    print("Checking content type")
    res = requests.get(content_url)
    content_type = res.headers['content-type']
    if content_type == "application/x-gzip":
        print("Found zipped content. Proceeding.")
    else:
        print("ERROR: Unexpected thing at URL.")
        exit(1)
    return content_type


def unzip_content(content_folder, filename):
    cmd = "tar -xzvf " + content_folder + "/" + filename + " -C " + content_folder
    exit_code = os.system(cmd)
    if exit_code == 0:
        print("Unzipped successfully.")
    else:
        print("ERROR: Unzipping failed. Exiting.")
        exit(1)
    cmd = "rm " + content_folder + "/" + filename
    os.system(cmd)

def download_content(content_url, content_folder, filename):
    content_type = "error"
    print("Downloading content bundle.")
    check_content_type(content_url, content_type)
    bundle = requests.get(content_url, allow_redirects=True)
    with open(content_folder + "/" + filename, "wb") as r:
        r.write(bundle.content)
    print("Finished downloading.")
    return filename

def build_container(stuff_path, name, tag, dockerfile_path, assets_path):
    cmd = "docker build -t " + name + ":" + tag + " -f " +  stuff_path + dockerfile_path + " " + stuff_path + assets_path
    print(cmd)
    exit_code = os.system(cmd)
    if exit_code == 0:
        print("Container built successfully.")
    else:
        print("ERROR: Container creation failed. Exiting.")
        exit(1)
    cmd = "docker images | grep " + name
    os.system(cmd)

def main():
    stuff_path = "./temp_deploy"
    repo = "https://github.com/bigpandaio/ops-exercise"
    content_url = "https://s3.eu-central-1.amazonaws.com/devops-exercise/pandapics.tar.gz"
    content_folder = stuff_path + "/public/images"
    filename = content_url.rsplit('/', 1)[1]

    # Downloading/preparing stuff
    create_deploy_folder(stuff_path)
    get_git_repo(repo, stuff_path)
    create_images_folder(stuff_path)
    download_content(content_url, content_folder, filename)
    unzip_content(content_folder,filename)

    # Working with docker
    print("Building docker containers")
    print("Building DB container")
    build_container(stuff_path, "mongo", "panda", "/db/Dockerfile", "/db/")
    print("Building node container")
    build_container(stuff_path, "node", "panda", "/Dockerfile ", " ")
    


if __name__ == "__main__":
    main()

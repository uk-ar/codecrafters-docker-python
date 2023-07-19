import requests

# name="ubuntu"
# tag="22.04"
tag = ""
def docker_pull(name,tag):
    name = "library/"+name

    response = requests.get(
        f'https://registry-1.docker.io/v2/{name}/manifests/{tag}')
    www_authenticate = response.headers['Www-Authenticate']
    realm, service, scope = www_authenticate.split(' ', 1)[1].split(',')

    # Extract the realm, service, and scope from the Www-Authenticate header
    realm = realm.split('=')[1].strip('"')
    service = service.split('=')[1].strip('"')
    scope = scope.split('=')[1].strip('"')
    print(realm, service, scope)

    # Step 2: Request a token from the Auth Service
    # headers = {'Docker-Distribution-API-Version':'registry/2.0'}
    auth_response = requests.get(f'{realm}?service={service}&scope={scope}')
    jwt = auth_response.json()['token']
    print(auth_response.json())

    # Step 3: Use the token to authenticate to the Docker Registry
    # headers = {'Authorization': f'Bearer {jwt}','Docker-Distribution-API-Version':'registry/2.0'}
    headers = {'Authorization': f'Bearer {jwt}',
            'Accept': 'application/vnd.oci.image.index.v1+json'}
    # headers = {'Authorization': f'Bearer {jwt}',
    # 'Accept':'application/vnd.docker.distribution.manifest.v2+json'}
    # headers = {'Authorization': f'Bearer {jwt}',
    # 'Accept':'application/vnd.docker.distribution.manifest.list.v2+json'}
    response = requests.get(
        f'https://registry-1.docker.io/v2/{name}/manifests/{tag}', headers=headers)

    print(response.json())

    manifest = {}
    for mani in response.json()["manifests"]:
        p = mani["platform"]
        if p["architecture"] == "amd64" and p["os"] == "linux":
            manifest = mani
            break
    digest = manifest["digest"]
    headers = {'Authorization': f'Bearer {jwt}', 'Accept': manifest["mediaType"]}
    response = requests.get(
        f'https://registry-1.docker.io/v2/{name}/manifests/{digest}', headers=headers)

    files=[]
    for i, layer in enumerate(response.json()["layers"]):
        print(f"downloading:{i}")
        headers = {'Authorization': f'Bearer {jwt}',
                'Accept': layer["mediaType"]}
        digest = layer["digest"]
        stream = requests.get(
            f'https://registry-1.docker.io/v2/{name}/blobs/{digest}', headers=headers, stream=True)
        file = f"{digest.split(':')[1]}.tar.gz"
        files.append(file)
        with open(file, "wb") as f:
            for chunk in stream.iter_content(chunk_size=8192):
                f.write(chunk)
    return files

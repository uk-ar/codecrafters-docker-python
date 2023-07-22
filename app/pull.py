#import requests
import json
import urllib.request

class Response:    
    def __init__(self,*,headers={},body=b'',stream=None):
        self.headers = headers
        #print("resp:init",headers,body,stream)
        self.body = body
        self.stream = stream
    def json(self):
        #print(self.body.read())
        return json.loads(self.body)
    def iter_content(self,*,chunk_size=8192):
        while True:
            ans = self.stream.read(chunk_size)
            if not ans:
                break
            yield ans


def get(url,*, headers={},stream=False): 
    #print(url,headers,stream)
    r = urllib.request.Request(url)
    r.headers = headers
    try:
        #with urllib.request.urlopen(r) as response:
        response = urllib.request.urlopen(r)
        #print("resp:",response.read())
        if stream:
            return Response(stream=response)
        return Response(body=response.read())
    except urllib.error.HTTPError as e:
        #print("err")
        #print(e.code,e.reason,e.headers,type(e.headers),e.headers.keys())
        #headers = BytesParser().parsebytes(e.headers)           
        return Response(headers=dict(e.headers.items()))

#stream = get(
#    f'https://registry-1.docker.io/v2/{name}/blobs/{digest}', headers=headers, stream=True)

def download(blobs,jwt,name):
    files=[]
    for i, digest in enumerate(blobs):
        #print(f"downloading:{i}")
        headers = {'Authorization': f'Bearer {jwt}'}
        stream = get(
            f'https://registry-1.docker.io/v2/{name}/blobs/{digest}', headers=headers, stream=True)
        file = f"{digest.split(':')[1]}.tar.gz"
        files.append(file)
        with open(file, "wb") as f:
            for chunk in stream.iter_content(chunk_size=8192):
                f.write(chunk)
    return files    

def docker_pull(name,tag):
    name = "library/"+name
    response = get(
        f'https://registry-1.docker.io/v2/{name}/manifests/{tag}')
    #print(response)
    #print(response.headers)
    www_authenticate = response.headers['www-authenticate']
    realm, service, scope = www_authenticate.split(' ', 1)[1].split(',')

    # Extract the realm, service, and scope from the Www-Authenticate header
    realm = realm.split('=')[1].strip('"')
    service = service.split('=')[1].strip('"')
    scope = scope.split('=')[1].strip('"')
    #print(realm, service, scope)

    # Step 2: Request a token from the Auth Service
    auth_response = get(f'{realm}?service={service}&scope={scope}')
    jwt = auth_response.json()['token']
    #print(auth_response.json())

    # Step 3: Use the token to authenticate to the Docker Registry
    # headers = {'Authorization': f'Bearer {jwt}','Docker-Distribution-API-Version':'registry/2.0'}
    headers = {'Authorization': f'Bearer {jwt}',
        'Accept': 'application/vnd.oci.image.index.v1+json'}
    # headers = {'Authorization': f'Bearer {jwt}',
    # 'Accept':'application/vnd.docker.distribution.manifest.v2+json'}
    # headers = {'Authorization': f'Bearer {jwt}',
    # 'Accept':'application/vnd.docker.distribution.manifest.list.v2+json'}
    response = get(
    f'https://registry-1.docker.io/v2/{name}/manifests/{tag}', headers=headers)

    #print(json.dumps(response.json(),indent=2))
    #print(response.json())
    resp = response.json()

    if resp["schemaVersion"]==1:
        blobs = [layer["blobSum"] for layer in resp["fsLayers"]]
        return download(blobs,jwt,name)

    manifest = {}
    for mani in response.json()["manifests"]:
        p = mani["platform"]
        if p["architecture"] == "amd64" and p["os"] == "linux":
            manifest = mani
            break
    digest = manifest["digest"]
    headers = {'Authorization': f'Bearer {jwt}', 'Accept': manifest["mediaType"]}
    response = get(
        f'https://registry-1.docker.io/v2/{name}/manifests/{digest}', headers=headers)

    files=[]
    for i, layer in enumerate(response.json()["layers"]):
        #print(f"downloading:{i}")
        headers = {'Authorization': f'Bearer {jwt}',
                'Accept': layer["mediaType"]}
        digest = layer["digest"]
        stream = get(
            f'https://registry-1.docker.io/v2/{name}/blobs/{digest}', headers=headers, stream=True)
        file = f"{digest.split(':')[1]}.tar.gz"
        files.append(file)
        with open(file, "wb") as f:
            for chunk in stream.iter_content(chunk_size=8192):
                f.write(chunk)
    return files

if __name__ == "__main__":
    docker_pull("alpine","latest")
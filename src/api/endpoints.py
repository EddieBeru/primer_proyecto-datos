from src.models.dungeons import CriptasResponse, DungeonGeneral, DungeonVersion
from src.api.client import Client


client = Client()

def listar_criptas():
    return client.make_request("criptas", model = CriptasResponse)

def info_cripta(id: str):
    return client.make_request(f"criptas/{id}", model = DungeonGeneral)

def version_cripta(id: str):
    return client.make_request(f"criptas/{id}/version", model = DungeonVersion)


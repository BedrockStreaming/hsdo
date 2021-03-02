from common.server_model import ServerModel
from typing import List

class SourceInterface:
    def getServers(self) -> List[ServerModel]:
        pass

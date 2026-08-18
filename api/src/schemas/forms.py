from typing import Annotated

from fastapi import Form


class OAuth2ClientCredentialsForm:
    def __init__(
        self,
        grant_type: Annotated[str, Form(pattern="^client_credentials$")],
        client_id: Annotated[str, Form(min_length=1)],
        client_secret: Annotated[str, Form(min_length=1)],
        scope: Annotated[str, Form()] = "",
    ) -> None:
        self.grant_type = grant_type
        self.client_id = client_id
        self.client_secret = client_secret
        self.scopes = {item for item in scope.split(" ") if item}

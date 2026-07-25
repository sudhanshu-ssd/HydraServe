from pydantic import BaseModel, ConfigDict, Field,EmailStr

class UserPrompt(BaseModel):
    prompt: str = Field(..., description="The user's prompt",max_length=1000) # will prolly remove the max_length constraint later, but for now, let's keep it to avoid groq rate limits
    model : str | None = Field(default="openai/gpt-oss-120b",description="the model sent by the user")
    model_temp : float | None = Field(default=0,description="temperature sent by th euser for the model")
    system_prompt : str | None = Field(default="You are an all around Help assistant")
    max_tokens : int | None = Field(default=1024)


class UserPromptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    response: str = Field(..., description="The response to the user's prompt",max_length=10000)


class Token(BaseModel):
    access_token:str = Field(...,description="access token that client/browser will get after logging in")
    token_type : str = Field(...,description="type of access token")

class User(BaseModel):
    username : str = Field(...,max_length=50,min_length=1,description="name of the user")

class UserRegister(User):
    email : EmailStr = Field(...,max_length=100,min_length=1,description="email of the user")
    password : str = Field(...,min_length=1,max_length=100,description="password set by user")

class RegisterResponse(User):
    pass

class ProjectReq(BaseModel):
    name : str  = Field(...,max_length=50,min_length=1,description="Name of the project")
    description : str | None = Field(default="No description provided",min_length=1,max_length=150,description="description of the project")

class ProjectResponse(ProjectReq):
    model_config = ConfigDict(from_attributes=True)
    project_id : int = Field(...,description="the id of project")
    

class APIresponse(BaseModel):
    api_key : str = Field(...,min_length=1,max_length=100,description="This will be only shown Once,User should copy this")


class ProjectUpdate(BaseModel):
    name : str | None = Field(max_length=50,min_length=1,description="Name of the project")
    description : str | None = Field(max_length=150,min_length=1)


class ForgotPassword(BaseModel):
    email : EmailStr = Field(...,min_length=1,max_length=100)

class ResetPassword(BaseModel):
    token :str = Field(...,min_length=1,max_length=70)
    new_password :str = Field(...,max_length=100,min_length=1)

class ChangePassword(BaseModel):
    old_password : str = Field(...,min_length=1,max_length=100)
    new_password : str = Field(...,min_length=1,max_length=100)

class Insert_Model(BaseModel):
    model_name : str 
    g_rpm : int 
    g_rpd : int 
    g_tpm : int
    g_tpd : int
    provider_id : int
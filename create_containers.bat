@echo off

REM Set the base image name
set imageName=buff2steam

REM Build the Docker image
docker build -t %imageName% .

REM Loop to create 100 containers
for /L %%i in (1,1,20) do (
    set containerName=buff2steam-%%i
    docker run --name=%containerName% --restart=always -d %imageName%
    
    REM Add a delay of 5 seconds
    timeout /nobreak /t 5 >nul
)
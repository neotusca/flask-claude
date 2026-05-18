### How to deploy
#### 1. make dir. & move to work-directory
        mkdir ~/flask-sample
        cd ~/flask-sample
#### 2. download this source
        git clone https://github.com/neotusca/flask-claude.git
#### 3. setting venv & activate environment
        virtualenv venv
        source venv/bin/activate
#### 4. install python packages
        cd flask-claude
        pip install -r requirements.txt   
#### 5. running flask-app        
        python3 app.py
#### 6. access test
        http://[server-public-ip]:5000 in web-browser 

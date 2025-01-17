from datetime import date
from connect_db import ConnectMysql
from flask import Flask, make_response, render_template, request, redirect
from jinja2 import Environment, FileSystemLoader

file_loader = FileSystemLoader("templates")
env = Environment(loader=file_loader)

template = env.get_template("index.html")

# 개인 환경에 따라 host 및 포트 정보 수정
HOST="127.0.0.1"
PORT=3306
USER="root"
PW="root"
DB="Nubisoft"

db = ConnectMysql()
conn, cur = db.mysql_create_session(HOST, PORT, USER, PW, DB)

app = Flask(__name__)

selectedGame = 0

@app.route("/", methods=['GET'])
def home():
  print("Get 요청")
  return render_template('index.html', context='')

@app.route("/", methods=['POST'])
def post_home():
  print("post 요청")
  return "끝"

@app.route("/login", methods=['GET'])
def get_login():
  user_id = request.cookies.get("user")

  if(user_id):
    component_name = "로그인 완료 상태"
    resp = redirect("/")
    return component_name
  else: 
    component_name = 'login'
    return render_template('index.html', context=component_name)

@app.route("/login", methods=['POST'])
def post_login():

  try:
    email = request.form['email']
    pw = request.form['pw']

    query = "SELECT userPassword, userId FROM User WHERE userEmail = %s"
    cur.execute(query, email)
    data = cur.fetchone()  # 이메일로 단일 사용자 조회

    if data is None:
        return "존재하지 않는 이메일입니다."
    elif data[0] == pw:
        resp =  redirect("/")
        resp.set_cookie("user", str(data[1]))
        global userid 
        userid = data[1]
        return resp
    else:
        return "잘못된 비밀번호입니다."

  except Exception as e:
    return f"Error : {e}"

@app.route("/signup")
def signup():
  component_name = 'signup'
  return render_template('index.html', context=component_name)

@app.route("/signup", methods=['POST'])
def post_signup():
  try:

    nickname = request.form['nickname']
    email = request.form['email']
    pw = request.form['pw']

    query = "SELECT userNickname FROM User WHERE userNickname = %s"
    cur.execute(query, nickname)
    nick_data = cur.fetchone()

    if nick_data is None:
      query = "SELECT userPassword FROM User WHERE userEmail = %s"
      cur.execute(query, email)
      email_data = cur.fetchone()

      if email_data is None:
        query = "INSERT INTO User (userEmail, userPassword, userNickname, userProfileImage) VALUES(%s, %s, %s, %s)"
        cur.execute(query, (email, pw, nickname, 1))
        result_data = cur.fetchall()
        
        if(result_data == []):
          cur.execute("commit;")
          return "회원가입 완료"
        else:
          print(result_data)
          return "회원가입 오류"

      elif email_data[0] == pw:
        return "이미 존재하는 사용자입니다."
    else:
      return "이미 존재하는 사용자입니다."

  except Exception as e:
    return f"Error : {e}"

@app.route("/logout", methods=['GET'])
def logout():
  resp = redirect("/")
  resp.delete_cookie("user")
  return resp

@app.route("/myaccount", methods=["GET"])
def get_user_info():
  user_id = request.cookies.get("user")

  query = "SELECT userEmail, userNickname from User where userId = %s"
  cur.execute(query, user_id)
  user_data = cur.fetchone()

  component_name = "editUser"
  return render_template("index.html", context=component_name, data={"email": user_data[0], "name": user_data[1]})

@app.route("/myaccount", methods=['POST'])
def post_user_info():
    user_id = request.cookies.get("user")

    nickname = request.form['nickname']
    email = request.form['email']

    query = "SELECT userNickname FROM User WHERE userNickname = %s"
    cur.execute(query, nickname)
    nick_data = cur.fetchone()

    if nick_data is None:
      query = "SELECT userPassword FROM User WHERE userEmail = %s"
      cur.execute(query, email)
      email_data = cur.fetchone()

      # update 문
      if email_data is None:
        query = "UPDATE User SET userEmail = %s, userNickname = %s where userId like %s"
        cur.execute(query, (email, nickname, user_id))
        result_data = cur.fetchall()
        
        if(result_data == []):
          cur.execute("commit;")
          return "회원수정 완료!"
        else:
          print(result_data)
          return "회원수정 오류"

      elif email_data[0] == pw:
        return "이미 사용하는 이메일 입니다."
    else:
      return "이미 사용하는 데이터 입니다."

    return ""

@app.route("/store", methods=["GET"])
def get_store():
  cur.execute('SELECT * FROM Game')
  data = cur.fetchall()
  
  result = []
  count = 0
  for rowdata in data:
    result.append([])
    result[count].append(rowdata[1])
    result[count].append(rowdata[2])
    count += 1

  component_name = 'store'
  return render_template('index.html', context=component_name, data={"gameinfo":result})

@app.route("/store", methods=["POST"])
def post_store():
  gameID = int(request.form["purchase"])
  print(gameID)

  userid = request.cookies.get("user")

  sqlQuery = 'INSERT INTO UserGame(userID, gameID, gamePlayTime) VALUES(%s, %s, %s)'

  selectedGame = int(gameID)

  args = (userid, selectedGame, "0:00")

  print(sqlQuery, args)

  cur.execute(sqlQuery, args)
  conn.commit()

  resp = redirect("/library")
  return resp

@app.route("/library")
def library():
  cur.execute('SELECT * FROM UserGame')
  data = cur.fetchall()
  
  result = []
  count = 0
  for rowdata in data:
    result.append([])
    result[count].append(rowdata[1])
    result[count].append(rowdata[2])
    count += 1

  cur.execute(f'SELECT gameID, gameName FROM Game')
  data = cur.fetchall()
  gamenameresult = []
  gamenamecount = 0
  for rowdata in data:
    gamenameresult.append([])
    gamenameresult[gamenamecount].append(rowdata[0])
    gamenameresult[gamenamecount].append(rowdata[1])
    gamenamecount += 1

  gamenames_dict = {game[0]: game[1] for game in gamenameresult}

  merged_result = []
  for gameid, gametime in result:
      if gameid in gamenames_dict:
          merged_result.append((gameid, str(gametime), gamenames_dict[gameid]))

  print(merged_result)

  component_name = 'library'
  return render_template('index.html', context=component_name, data={"usergameinfo":merged_result})

@app.route("/achieve", methods=["GET"])
def get_achieve():
  cur.execute('SELECT * FROM Achievement')
  data = cur.fetchall()
  
  result = []
  count = 0
  for rowdata in data:
    result.append([])
    result[count].append(rowdata[1])
    result[count].append(rowdata[2])
    count += 1

  component_name = 'achieve'
  return render_template('index.html', context=component_name, data={"achieveinfo":result})

@app.route("/achieve", methods=["POST"])
def post_achieve():
  achieveID = request.form["button"]

  userid = request.cookies.get("user")
  
  sqlQuery = 'INSERT INTO UserAchievement(userID, achievementID, achieveDate, achieveStatus) VALUES(%s, %s, %s, %s)'
  args = (userid, achieveID, date.today(), 1)

  cur.execute(sqlQuery, args)
  conn.commit()

  resp = redirect("/library")
  return resp

@app.route("/libraryUser")
def libraryUser():
  cur.execute('SELECT * FROM UserAchievement')
  data = cur.fetchall()
  
  result = []
  count = 0
  for rowdata in data:
    result.append([])
    result[count].append(rowdata[1])
    result[count].append(rowdata[2])
    count += 1

  cur.execute(f'SELECT achievementID, achievementName FROM Achievement')
  data = cur.fetchall()
  achinameresult = []
  achinamecount = 0

  for rowdata in data:
    achinameresult.append([])
    achinameresult[achinamecount].append(rowdata[0])
    achinameresult[achinamecount].append(rowdata[1])
    achinamecount += 1

  achinames_dict = {achi[0]: achi[1] for achi in achinameresult}

  merged_result = []
  for achiid, achitime in result:
      if achiid in achinames_dict:
          merged_result.append((achiid, str(achitime), achinames_dict[achiid]))

  print(merged_result)

  component_name = 'libraryUser'
  return render_template('index.html', context=component_name, data={"userachieveinfo":merged_result})

if __name__ == '__main__':
  app.run(port=8080, debug=True)
import sqlite3
from flask import Flask, render_template
import os
import flask

from requests import request


app = Flask(__name__)

def recup_base():
    return os.listdir('./data/db')

#fonction permetant l'affichage des test pre et post réalisé et stock en mémoire
def show(nomClient,statut):
    result = []
    bd = './data/db/'+str(nomClient)
    con = sqlite3.connect(bd)
    cur = con.cursor()
    if statut == 'post':
        cur.execute("SELECT id,date FROM TEST WHERE statut like 'post'")
        result_tmp = cur.fetchall()
    else:
        cur.execute("SELECT id,date FROM TEST WHERE statut like 'pre'")
        result_tmp = cur.fetchall()
    for row in result_tmp:
        result.append({'ID': row[0], 'DATE' :row[1]})
    return result

#fonction permattant de selection un test a partir de l'id de la base de données
def select_one(nomClient,id):
    id = str(id)
    bd = './data/db/'+str(nomClient)+'.db'
    con = sqlite3.connect(bd)
    cur = con.cursor()
    cur.execute("SELECT * FROM TEST where id = ?",id)
    selected = cur.fetchall()
    return selected

#fonction permettant la convertion en tableau des résultat stocké en chaine de caractére
def parse_retour_bd(selected):
    converti = list(list(selected))[0]
    return eval(converti[1])

#fonction permettant la concaténation de eux test d'url 
def compare_url(test_pre, test_post):
    result_url = []
    for item in test_pre:
        for item2 in test_post:
            result_url.append({'typeTest': 'URL','url': item['url'], 'port': 'HTTP/HTTPS', 'result_pre': item['result'], 'result_post': item2['result']})
            break
    return result_url

#fonction permettant la concaténation de eux test d'ip 
def compare_ip(test_pre, test_post):
    result_ip = []
    for item in test_pre:
        for item2 in test_post:
            result_ip.append({'typeTest': 'Ping','desc': item['desc'], 'ip': item['ip'], 'port': 'ICMP', 'result_pre': item['result'], 'result_post': item2['result']})
            break
    return result_ip

#fonction permettant la concaténation de eux test d'application 
def compare_app(test_pre, test_post):
    result_app = []
    for item in test_pre:
        for item2 in test_post:
            result_app.append({'typeTest': 'NC', 'ip': item['ip'], 'port': item['port'], 'result_pre': item['result'], 'result_post': item2['result']})
            break
    return result_app        

#fonction permettant affiche les différence entre 2 tests
def delta1(resultat_pre, resultat_post):
    delta = []
    for i in range(0,len(resultat_post)):
        delta_tmp = []
        for j in range(0,len(resultat_post[i])):
            e_pre = resultat_pre[i][j]
            e_post = resultat_post[i][j]
            if (e_post.get('result') != e_pre.get('result')):
                if i == 0: 
                    delta_tmp.append({'typeTest': e_post.get('typeTest'),'url': e_post.get('url'), 'port': 'HTTP/HTTPS', 'result':  'avant '+ e_pre.get('result') + ' ---> aprés ' + e_post.get('result')})
                elif i == 1: 
                    delta_tmp.append({'typeTest': 'NC', 'ip': e_post.get('ip'), 'port': e_post.get('port'), 'result':  'avant '+ e_pre.get('result') + ' ---> aprés ' + e_post.get('result')})
                elif i == 2:
                    delta_tmp.append({'typeTest': 'Ping','desc': e_post.get('desc'), 'ip': e_post.get('ip'), 'port': 'ICMP', 'result':  'avant '+ e_pre.get('result') + ' ---> aprés ' + e_post.get('result')})
        delta.append(delta_tmp)
    return delta   

########################## rendu page d'acceuil ##########################
@app.route('/')
def index():
    return render_template("pages/home.html", dbs = recup_base())

########################## rendu page client ##########################
@app.route('/client', methods=["POST","GET"])
def client():
    nomdb = flask.request.args['nomc']
    nomc = nomdb.split(".")
    pre = show(nomdb,'pre')
    post = show(nomdb,'post')
    return render_template("pages/client.html", nomc =nomc[0], pre = pre, post = post)

########################## rendu page detail ##########################
@app.route('/testdetails/<cname>/<type>/<int:id>')
def test(cname, type,id):
    col_ip = ['Type de test','Description', 'IP', 'Port','Résultat (OK/NOK)']
    col_url = ['Type de test','URL', 'Port','Résultat (OK/NOK)']
    col_app = ['Type de test','IP', 'Port','Résultat (OK/NOK)']
    resultat = parse_retour_bd(select_one(cname,id))
    return render_template("pages/testdetails.html", cname = cname, type = type, id = id, 
                           col_ip =col_ip, col_url = col_url, col_app = col_app,
                           ligne_ip = resultat[2], ligne_url = resultat[0], ligne_app = resultat[1])
    
########################## rendu page compare ########################## 
@app.route('/compare/<cname>')
def compare(cname):
    col_ip = ['Type de test','Description', 'IP', 'Port','Résultat Pre (OK/NOK)', 'Résultat Post (OK/NOK)']
    col_url = ['Type de test','URL', 'Port','Résultat Pre (OK/NOK)', 'Résultat Post (OK/NOK)']
    col_app = ['Type de test','IP', 'Port','Résultat Pre (OK/NOK)', 'Résultat Post (OK/NOK)']
    dico = flask.request.args
    result_pre = parse_retour_bd(select_one(cname, dico['pre']))
    result_post = parse_retour_bd(select_one(cname,dico['post']))
    url = compare_url(result_pre[0], result_post[0])
    ip = compare_ip(result_pre[2], result_post[2])
    app = compare_app(result_pre[1], result_post[1])
    return render_template("pages/compare.html", cname = cname, id_pre = dico['pre'], id_post = dico['post'], 
                           col_ip =col_ip, col_url = col_url, col_app = col_app,
                           url = url, ip = ip, app = app
                           )
########################## rendu page delta ##########################
@app.route('/delta/<cname>')
def delta(cname): 
    col_ip = ['Type de test','Description', 'IP', 'Port','Résultat']
    col_url = ['Type de test','URL', 'Port','Résultat']
    col_app = ['Type de test','IP', 'Port','Résultat']
    dico = flask.request.args
    result_pre = parse_retour_bd(select_one(cname, dico['pre']))
    result_post = parse_retour_bd(select_one(cname,dico['post']))
    resultat = delta1(result_pre,result_post)
    return render_template("pages/delta.html", cname = cname, id_pre = dico['pre'], id_post = dico['post'],
                           col_ip =col_ip, col_url = col_url, col_app = col_app,
                           ligne_ip = resultat[2], ligne_url = resultat[0], ligne_app = resultat[1])

if __name__ == '__main__': 
    app.run(Debug=True)
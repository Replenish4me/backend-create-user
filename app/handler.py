import boto3
import json
import pymysql
import os
import re
import hashlib

def lambda_handler(event, context):
    
    # Leitura dos parâmetros da requisição
    nome = event['nome']
    email = event['email']
    senha = event['senha']
    endereco = event['endereco']
    telefone = event['telefone']

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        response = {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"message": "O email fornecido é inválido"}),
        }
        return response
    
    if not re.match(r"\(\d{2}\) \d{5}-\d{4}", telefone):
        response = {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"message": "O telefone fornecido é inválido"}),
        }
        return response
    
    if not re.match(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$", senha):
        response = {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"message": "A senha fornecida é inválida. Ela deve conter pelo menos 8 caracteres, uma letra e um número"}),
        }
        return response
    
    senha = hashlib.sha256(bytes(senha, 'utf-8')).hexdigest()

    secretsmanager = boto3.client('secretsmanager')
    response = secretsmanager.get_secret_value(SecretId=f'replenish4me-db-password-{os.environ.get("env", "dev")}')
    db_password = response['SecretString']
    rds = boto3.client('rds')
    response = rds.describe_db_instances(DBInstanceIdentifier=f'replenish4medatabase{os.environ.get("env", "dev")}')
    endpoint = response['DBInstances'][0]['Endpoint']['Address']
    # Conexão com o banco de dados
    with pymysql.connect(
        host=endpoint,
        user='admin',
        password=db_password,
        database='replenish4me'
    ) as conn:
        
        # Criação de um novo usuário
        with conn.cursor() as cursor:
            sql = "INSERT INTO Usuarios (nome, email, senha, endereco, telefone) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (nome, email, senha, endereco, telefone))
            conn.commit()
        

    # Retorno da resposta da função
    response = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({"message": "Usuário criado com sucesso"}),
    }
    return response

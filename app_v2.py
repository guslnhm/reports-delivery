import os
import os
from decimal import Decimal, InvalidOperation
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from dotenv import load_dotenv
import gspread
from openpyxl import Workbook, load_workbook #excluir
import psycopg2 # excluir
from psycopg2.extras import execute_values

# .env
load_dotenv()
PGHOST = os.getenv("PGHOST")
PGPORT = os.getenv("PGPORT")
PGDATABASE = os.getenv("PGDATABASE")
PGUSER = os.getenv("PGUSER")
PGPASSWORD = os.getenv("PGPASSWORD")

DSN = f"host={PGHOST} port={PGPORT} dbname={PGDATABASE} user={PGUSER} password={PGPASSWORD}"

TABLE = "public.financeiro_mensal"
COLS = ("valor_liquido", "recebido_via_loja", "valor_bruto", "repassados_ao_ifood", "repasse", "taxa_repasse", "custo_ifood", "tempo_medio_entrega")

def insert_db(vliq, receb, vbrt, rps_ifd, repasse, taxa_rps, custo_ifd, entr):
    sql = f"""
        INSERT INTO {TABLE}
    """
    conn = None
    try:
        conn = psycopg2.connect(DSN)
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (vliq, receb, vbrt, rps_ifd, repasse, taxa_rps, custo_ifd, entr))
    except Exception as e:
        raise e

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Seu Sucesso Delivery 🚀 — Relatório financeiro")
        self.config(padx=50, pady=50)

        # valor líquido
        ttk.Label(self, text="Valor líquido:").pack(pady=(10,0))
        self.valor_liquido = ttk.Entry(self)
        self.valor_liquido.pack()

        # recebido via loja
        ttk.Label(self, text="Valor recebido via loja:").pack(pady=(10,0))
        self.recebido_loja = ttk.Entry(self)
        self.recebido_loja.pack()

        # valor bruto
        ttk.Label(self, text="Valor bruto:").pack(pady=(10,0))
        self.valor_bruto = ttk.Entry(self)
        self.valor_bruto.pack()

        # repassados ao ifood
        ttk.Label(self, text="Valores repassados ao iFood:").pack(pady=(10,0))
        self.repassados = ttk.Entry(self)
        self.repassados.pack()

        # tempo médio de entrega
        ttk.Label(self, text="Tempo médio de entrega:").pack(pady=(10,0))
        self.entrega = ttk.Entry(self)
        self.entrega.pack()

        ttk.Button(self, text="Calcular", command=self.calcular).pack(pady=15)

        def calcular(self):
            print("Elaborar requisitos da função")
            
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
        INSERT INTO {TABLE} ({', '.join(COLS)})
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """
    conn = None
    try:
        conn = psycopg2.connect(DSN)
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (vliq, receb, vbrt, rps_ifd, repasse, taxa_rps, custo_ifd, entr))
    except Exception as e:
        raise e
    finally:
        if conn:
            conn.close()

def run_query(sql, params=None, fetch="all"):
    with psycopg2.connect(DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            if fetch == "one":
                return cur.fetchone()
            elif fetch == "all":
                return cur.fetchall()
            return None

# queries para combobox
SQL_MESES = """
SELECT DISTINCT mes
FROM financeiro_mensal;
"""

SQL_LOJAS = """
SELECT DISTINCT loja
FROM financeiro_mensal
WHERE mes = %s
ORDER BY loja;
"""

SQL_OPERACOES = """
SELECT DISTINCT operacao
FROM financeiro_mensal
WHERE mes = %s AND loja = %s
ORDER BY operacao;
"""

SQL_GET_VALORES = """
"""

SQL_UPDATE_VALORES = """
"""

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Seu Sucesso Delivery 🚀 — Relatório financeiro")
        self.config(padx=50, pady=50)

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        #comboboxes
        ttk.Label(frm, text="Mês:").grid(row=0, column=0, sticky="w")
        self.cb_mes = ttk.Combobox(frm, state="readonly", width=28)
        self.cb_mes.grid(row=0, column=1, sticky="ew", padx=6)

        ttk.Label(frm, text="Loja:").grid(row=1, column=0, sticky="w")
        self.cb_loja = ttk.Combobox(frm, state="readonly", width=28)
        self.cb_loja.grid(row=1, column=1, sticky="ew", padx=6)

        ttk.Label(frm, text="Operação:").grid(row=2, column=0, sticky="w")
        self.cb_operacao = ttk.Combobox(frm, state="readonly", width=28)
        self.cb_operacao.grid(row=2, column=1, sticky="ew", padx=6)

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
        self.repassados_ifd = ttk.Entry(self)
        self.repassados_ifd.pack()

        # tempo médio de entrega
        ttk.Label(self, text="Tempo médio de entrega:").pack(pady=(10,0))
        self.entrega = ttk.Entry(self)
        self.entrega.pack()

        ttk.Button(self, text="Calcular", command=self.calcular).pack(pady=15)

        self.cb_mes.bind("<<ComboboxSelected>>", lambda e: self._load_lojas())
        self.cb_loja.bind("<<ComboboxSelected>>", lambda e: self._load_operacoes())


        self._load_meses()
    
    def _load_meses(self):
        try:
            rows = run_query(SQL_MESES, fetch="all")
            meses = [r[0] for r in rows]
            self.cb_mes["values"] = meses
            if meses:
                self.cb_mes.current(0)
                self._load_lojas()
        except Exception as e:
            messagebox.showerror("Erro ao carregar meses", str(e))
    
    def _load_lojas(self):
        mes = (self.cb_mes.get() or "").strip()
        self.cb_loja["values"] = []
        self.cb_operacao["values"] = []
        if not mes:
            return
        
        rows = run_query(
            """
            SELECT DISTINCT loja
            FROM financeiro_mensal
            WHERE LOWER(TRIM(mes)) = LOWER(TRIM(%s))
            ORDER BY loja;
            """,
            (mes,),
            fetch="all"
        )
        lojas = [ (r[0] or "").strip() for r in rows ]
        self.cb_loja["values"] = lojas
        #self.cb_operacao["values"] = []
        if lojas:
            self.cb_loja.current(0)
            self._load_operacoes()
    
    def _load_operacoes(self):
        mes = (self.cb_mes.get() or "").strip()
        loja = (self.cb_loja.get() or "").strip()
        self.cb_operacao["values"] = []
        if not (mes and loja):
            return
        
        rows = run_query(
            """
            SELECT DISTINCT operacao
            FROM financeiro_mensal
            WHERE LOWER(TRIM(mes))  = LOWER(TRIM(%s))
            AND LOWER(TRIM(loja)) = LOWER(TRIM(%s))
            ORDER BY operacao;
            """,
            (mes, loja),
            fetch="all"
        )
        operacoes = [ (r[0] or "").strip() for r in rows ]
        self.cb_operacao["values"] = operacoes

        if operacoes:
            self.cb_operacao.current(0)

    def calcular(self):
        mes = self.cb_mes.get().strip()
        loja = self.cb_loja.get().strip()
        operacao = self.cb_operacao.get().strip()

        sql = """
            SELECT valor_itens
            FROM financeiro_mensal
            WHERE mes = %s AND loja = %s AND operacao = %s;
        """

        row = run_query(sql, (mes, loja, operacao), fetch="one")

        valor_itens = Decimal(row[0])

        # ordem: vliq, receb, vbrt, rps_ifood, repasse, taxa_rps, custo_ifd, entr
        vliq = Decimal((self.valor_liquido.get()).replace('R$','').replace('.','').replace(',','.').strip())
        vbru = Decimal((self.valor_bruto.get()).replace('R$','').replace('.','').replace(',','.').strip())
        receb = Decimal((self.recebido_loja.get()).replace('R$','').replace('.','').replace(',','.').strip())
        repas_ifd = Decimal((self.repassados_ifd.get()).replace('R$','').replace('.','').replace(',','.').strip())
        entr = Decimal((self.entrega.get()).replace('R$','').replace('.','').replace(',','.').strip())
        #print(type(vliq))
        #print(vliq)
        #já tenho: valor líquido, valor bruto, recebido loja, repassado ao ifood e entrega
        #falta: repasse, taxa de repasse e custo ifood
        repasse = vliq + receb
        taxa_repasse = repasse/(vbru-repas_ifd)
        custo_ifd = 1-taxa_repasse
        #insert_db()
        print(f"Valor líquido = {vliq}\nRecebido via loja = {receb}\nValor bruto = {vbru}\nRepassado ao iFood = {repas_ifd}\nValor dos itens = {valor_itens}\nTaxa de repasse = {taxa_repasse}\nCusto iFood={custo_ifd}")


if __name__ == '__main__':
    App().mainloop()
import os
import os
from decimal import Decimal, InvalidOperation
import tkinter as tk
from tkinter import ttk, messagebox
from dotenv import load_dotenv
import psycopg2

load_dotenv()
PGHOST = os.getenv("PGHOST")
PGPORT = os.getenv("PGPORT")
PGDATABASE = os.getenv("PGDATABASE")
PGUSER = os.getenv("PGUSER")
PGPASSWORD = os.getenv("PGPASSWORD")

DSN = f"host={PGHOST} port={PGPORT} dbname={PGDATABASE} user={PGUSER} password={PGPASSWORD}"

TABLE = "analytics.financeiro_mensal"

def update_db(mes, loja, operacao, vliq, receb, vbrt, rps_ifd, repasse, taxa_rps, custo_ifd, entr, nv_cl):
    sql = f"""
        UPDATE {TABLE}
            SET valor_liquido = COALESCE(%s, valor_liquido),
                recebido_via_loja = COALESCE(%s, recebido_via_loja),
                valor_bruto = COALESCE(%s, valor_bruto),
                repassados_ao_ifood = COALESCE(%s, repassados_ao_ifood),
                repasse = COALESCE(%s, repasse),
                taxa_repasse = COALESCE(%s, taxa_repasse),
                custo_ifood = COALESCE(%s, custo_ifood),
                tempo_medio_entrega = COALESCE(%s, tempo_medio_entrega),
                novos_clientes = COALESCE(%s, novos_clientes)
        WHERE mes = %s
            AND loja = %s
            AND operacao = %s;
    """
    params = (
        vliq, receb, vbrt, rps_ifd, repasse, taxa_rps, custo_ifd, entr, nv_cl, mes, loja, operacao
    )
    conn = None
    try:
        conn = psycopg2.connect(DSN)
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
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
FROM analytics.financeiro_mensal;
"""

SQL_LOJAS = """
SELECT DISTINCT loja
FROM analytics.financeiro_mensal
WHERE mes = %s
ORDER BY loja;
"""

SQL_OPERACOES = """
SELECT DISTINCT operacao
FROM analytics.financeiro_mensal
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
        self.config(padx=50, pady=50, bg="#0F161F")

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        self.operacao_unica = None

        self.loja_anterior = ""
        self.operacao_anterior = ""

        # botão de limpar
        ttk.Button(self, text="Limpar", command=self.limpar).pack(pady=15)

        #comboboxes
        ttk.Label(frm, text="Mês:").grid(row=0, column=0, sticky="w")
        self.cb_mes = ttk.Combobox(frm, state="readonly", width=28)
        self.cb_mes.grid(row=0, column=1, sticky="ew", padx=6)

        ttk.Label(frm, text="Loja:").grid(row=1, column=0, sticky="w")
        self.cb_loja = ttk.Combobox(frm, state="readonly", width=28)
        self.cb_loja.grid(row=1, column=1, sticky="ew", padx=6)

        '''ttk.Label(frm, text="Operação:").grid(row=2, column=0, sticky="w")
        self.cb_operacao = ttk.Combobox(frm, state="readonly", width=28)
        self.cb_operacao.grid(row=2, column=1, sticky="ew", padx=6)'''

        self.lbl_operacao = ttk.Label(frm, text="Operação:")
        self.cb_operacao = ttk.Combobox(frm, state="readonly", width=28)

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

        # novos clientes
        ttk.Label(self, text="Novos clientes:").pack(pady=(10,0))
        self.novos_clientes = ttk.Entry(self)
        self.novos_clientes.pack()

        ttk.Button(self, text="Calcular", command=self.calcular).pack(pady=15)

        self.lbl_resultado = ttk.Label(self, text="Resultado aparecerá aqui")
        self.lbl_resultado.pack(pady=10)

        '''self.lbl_resultado = ttk.Entry(self, state="readonly")
        self.lbl_resultado.pack()'''

        self.cb_mes.bind("<<ComboboxSelected>>", lambda e: self._load_lojas())
        self.cb_loja.bind("<<ComboboxSelected>>", lambda e: self._load_operacoes())


        self._load_meses()

    def hide_cbx(self, operacao_unica):
        if self.lbl_operacao.winfo_ismapped():
            self.lbl_operacao.grid_remove()
        if self.cb_operacao.winfo_ismapped():
            self.cb_operacao.grid_remove()

        self.operacao_unica = operacao_unica

        self.adjust_layout()
    
    def show_cbx(self, operacoes):
        self.lbl_operacao.grid(row=2, column=0, sticky="w", pady=(10,0))
        self.cb_operacao.grid(row=2, column=1, sticky="ew", padx=6, pady=(10,0))

        self.cb_operacao['values'] = operacoes
        if operacoes:
            self.cb_operacao.set(operacoes[0])
        
        self.operacao_unica = None

        self.adjust_layout()
    
    def adjust_layout(self):
        pass


    def limpar(self):
        self.valor_liquido.delete(0, tk.END)
        self.recebido_loja.delete(0, tk.END)
        self.valor_bruto.delete(0, tk.END)
        self.repassados_ifd.delete(0, tk.END)
        self.entrega.delete(0, tk.END)
        self.novos_clientes.delete(0, tk.END)

    def parse_decimal(self, valor_str):
        valor_str = valor_str.strip()
        if valor_str == "":
            return None
        try:
            return Decimal(
                valor_str
                .replace("R$", "")
                .replace(".", "")
                .replace(",", ".")
                .replace("-", "")
                .strip()
            )
        except InvalidOperation:
            return "erro"

    
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
        self.loja_anterior = self.cb_loja.get().strip()
        self.operacao_anterior = self.cb_operacao.get().strip() if not self.operacao_unica else self.operacao_unica

        mes = (self.cb_mes.get() or "").strip()
        self.cb_loja["values"] = []

        self.operacao_unica = None
        if self.cb_operacao.winfo_ismapped():
            self.cb_operacao.set('')

        if not mes:
            return
        
        rows = run_query(
            """
            SELECT DISTINCT loja
            FROM analytics.financeiro_mensal
            WHERE LOWER(TRIM(mes)) = LOWER(TRIM(%s))
            ORDER BY loja;
            """,
            (mes,),
            fetch="all"
        )
        lojas = [ (r[0] or "").strip() for r in rows ]
        self.cb_loja["values"] = lojas
        '''if lojas:
            self.cb_loja.current(0)
            self._load_operacoes()'''
        
        if lojas:
            if self.loja_anterior in lojas:
                self.cb_loja.set(self.loja_anterior)
            else:
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
            FROM analytics.financeiro_mensal
            WHERE LOWER(TRIM(mes))  = LOWER(TRIM(%s))
            AND LOWER(TRIM(loja)) = LOWER(TRIM(%s))
            ORDER BY operacao;
            """,
            (mes, loja),
            fetch="all"
        )
        operacoes = [ (r[0] or "").strip() for r in rows ]
        
        if len(operacoes) == 1:
            self.hide_cbx(operacoes[0])
        else:
            self.show_cbx(operacoes)
            if operacoes and self.operacao_anterior in operacoes:
                self.cb_operacao.set(self.operacao_anterior)

    def calcular(self):
        mes = self.cb_mes.get().strip()
        loja = self.cb_loja.get().strip()
        
        if self.operacao_unica:
            operacao = self.operacao_unica
        else:
            operacao = self.cb_operacao.get().strip()
        
        if not operacao:
            messagebox.showerror("Erro", "Nenhuma operação selecionada")
            return

        sql = """
            SELECT valor_itens
            FROM analytics.financeiro_mensal
            WHERE mes = %s AND loja = %s AND operacao = %s;
        """

        row = run_query(sql, (mes, loja, operacao), fetch="one")

        valor_itens = Decimal(row[0])

        # ordem: vliq, receb, vbrt, rps_ifood, repasse, taxa_rps, custo_ifd, entr, novos_clientes
        '''vliq = Decimal((self.valor_liquido.get()).replace('R$','').replace('.','').replace(',','.').strip())
        vbru = Decimal((self.valor_bruto.get()).replace('R$','').replace('.','').replace(',','.').strip())
        receb = Decimal((self.recebido_loja.get()).replace('R$','').replace('.','').replace(',','.').strip())
        repas_ifd = Decimal((self.repassados_ifd.get()).replace('-','').replace('R$','').replace('.','').replace(',','.').strip())
        entr = Decimal((self.entrega.get()).strip())
        nv_cl = Decimal((self.novos_clientes.get()).strip())'''

        vliq = self.parse_decimal(self.valor_liquido.get())
        vbru = self.parse_decimal(self.valor_bruto.get())
        receb = self.parse_decimal(self.recebido_loja.get())
        repas_ifd = self.parse_decimal(self.repassados_ifd.get())
        entr = self.parse_decimal(self.entrega.get())
        nv_cl = self.parse_decimal(self.novos_clientes.get())

        repasse = None
        taxa_repasse = None
        custo_ifd = None
        
        if vliq is not None and receb is not None:
            repasse = vliq + receb
        
        if repasse is not None and vbru is not None and repas_ifd is not None:
            taxa_repasse = repasse/(vbru-repas_ifd)

        if taxa_repasse is not None:
            custo_ifd = 1-taxa_repasse

        #cabeçalho da função:
        #def update_db(vliq, receb, vbrt, rps_ifd, repasse, taxa_rps, custo_ifd, entr, nv_cl)

        update_db(mes, loja, operacao, vliq, receb, vbru, repas_ifd, repasse, taxa_repasse, custo_ifd, entr, nv_cl)
        
        self.lbl_resultado.config(text=f"Taxa de repasse = {taxa_repasse}\nCusto iFood={custo_ifd}")


if __name__ == '__main__':
    App().mainloop()
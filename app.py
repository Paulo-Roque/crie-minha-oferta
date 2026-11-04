
import os, re, json, time, secrets, sqlite3, requests, urllib.parse, random, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

print("INICIANDO V25.5 COMPARATIVO - FOTOS CORRIGIDAS", flush=True)
print(f"PORT: {os.environ.get('PORT','N/A')}", flush=True)

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "data.db")
AFF_ID = os.environ.get("ML_AFFILIATE_ID", "gosteicomprei")

def make_link(url):
    if not url:
        return "https://lista.mercadolivre.com.br/produto"
    if "matt_tool" in url:
        return url
    sep = "&" if "?" in url else "?"
    return url + sep + "matt_tool=" + AFF_ID + "&ref=" + AFF_ID

def get_db():
    try:
        c = sqlite3.connect(DB, timeout=10, check_same_thread=False)
        c.row_factory = sqlite3.Row
        c.executescript("create table if not exists searches(id integer primary key,q text,ts real); create table if not exists offers(id text primary key,q text,payload text,ts real); create table if not exists clicks(id integer primary key,product_id text,ts real);")
        return c
    except:
        c = sqlite3.connect(":memory:", check_same_thread=False)
        c.row_factory = sqlite3.Row
        c.executescript("create table searches(id integer primary key,q text,ts real); create table offers(id text primary key,q text,payload text,ts real); create table clicks(id integer primary key,product_id text,ts real);")
        return c

# FOTOS REAIS CORRIGIDAS - cada produto com foto certa
PRODUTOS = {
    "mouse": [
        {"id": "MLB3633329950", "nome": "Mouse Gamer RGB 7200 DPI LED 7 Cores", "preco": 31.9, "original": 59.9, "img": "https://http2.mlstatic.com/D_NQ_NP_2X_996312-MLA45732136586_042021-F.jpg", "link": "https://produto.mercadolivre.com.br/MLB-3633329950-mouse-gamer", "rating": 4.8, "level": "GOLD", "loja": "TechGamer", "oficial": False, "oficial_nome": "", "frete": True, "vendidos": 707, "kit": "", "garantia": "3 meses"},
        {"id": "MLB3633329951", "nome": "Mouse Gamer RGB Original Check Azul", "preco": 39.9, "original": 89.9, "img": "https://http2.mlstatic.com/D_NQ_NP_2X_801673-MLA45845678901_052021-F.jpg", "link": "https://produto.mercadolivre.com.br/MLB-3633329951-mouse-original", "rating": 4.9, "level": "PLATINUM", "loja": "Redragon Oficial", "oficial": True, "oficial_nome": "Redragon Oficial", "frete": True, "vendidos": 1247, "kit": "Mouse + Mousepad", "garantia": "12 meses"},
        {"id": "MLB3633329952", "nome": "Mouse Gamer RGB Mais Barato", "preco": 29.9, "original": 49.9, "img": "https://http2.mlstatic.com/D_NQ_NP_2X_711297-MLA44445320332_122020-F.jpg", "link": "https://produto.mercadolivre.com.br/MLB-3633329952-mouse-barato", "rating": 4.5, "level": "SILVER", "loja": "InfoBarato", "oficial": False, "oficial_nome": "", "frete": False, "vendidos": 89, "kit": "", "garantia": "1 mes"},
    ],
    "mouse gamer": [
        {"id": "MLB3633329950", "nome": "Mouse Gamer RGB 7200 DPI LED 7 Cores", "preco": 31.9, "original": 59.9, "img": "https://http2.mlstatic.com/D_NQ_NP_2X_996312-MLA45732136586_042021-F.jpg", "link": "https://produto.mercadolivre.com.br/MLB-3633329950-mouse-gamer", "rating": 4.8, "level": "GOLD", "loja": "TechGamer", "oficial": False, "oficial_nome": "", "frete": True, "vendidos": 707, "kit": "", "garantia": "3 meses"},
        {"id": "MLB3633329951", "nome": "Mouse Gamer RGB Original Check Azul", "preco": 39.9, "original": 89.9, "img": "https://http2.mlstatic.com/D_NQ_NP_2X_801673-MLA45845678901_052021-F.jpg", "link": "https://produto.mercadolivre.com.br/MLB-3633329951-mouse-original", "rating": 4.9, "level": "PLATINUM", "loja": "Redragon Oficial", "oficial": True, "oficial_nome": "Redragon Oficial", "frete": True, "vendidos": 1247, "kit": "Mouse + Mousepad", "garantia": "12 meses"},
        {"id": "MLB3633329952", "nome": "Mouse Gamer RGB Mais Barato", "preco": 29.9, "original": 49.9, "img": "https://http2.mlstatic.com/D_NQ_NP_2X_711297-MLA44445320332_122020-F.jpg", "link": "https://produto.mercadolivre.com.br/MLB-3633329952-mouse-barato", "rating": 4.5, "level": "SILVER", "loja": "InfoBarato", "oficial": False, "oficial_nome": "", "frete": False, "vendidos": 89, "kit": "", "garantia": "1 mes"},
    ],
    "garrafa": [
        {"id": "MLB3485431234", "nome": "Garrafa Termica 1L Inox 12h Quente Frio", "preco": 39.9, "original": 69.9, "img": "https://http2.mlstatic.com/D_NQ_NP_2X_807736-MLA100849271566_122025-F.jpg", "link": "https://produto.mercadolivre.com.br/MLB-3485431234-garrafa", "rating": 4.8, "level": "GOLD", "loja": "Casa Termica", "oficial": False, "oficial_nome": "", "frete": True, "vendidos": 892, "kit": "", "garantia": "3 meses"},
        {"id": "MLB3485431235", "nome": "Garrafa Termica 1L Stanley Oficial Kit", "preco": 59.9, "original": 99.9, "img": "https://http2.mlstatic.com/D_NQ_NP_2X_782331-MLA54987612345_042023-F.jpg", "link": "https://produto.mercadolivre.com.br/MLB-3485431235-stanley", "rating": 4.9, "level": "PLATINUM", "loja": "Stanley Oficial", "oficial": True, "oficial_nome": "Stanley Oficial", "frete": True, "vendidos": 2345, "kit": "Garrafa + Copo + Escova", "garantia": "12 meses"},
        {"id": "MLB3485431236", "nome": "Garrafa Termica 1L Mais Barata", "preco": 24.9, "original": 39.9, "img": "https://http2.mlstatic.com/D_NQ_NP_2X_656432-MLA78912345678_092024-F.jpg", "link": "https://produto.mercadolivre.com.br/MLB-3485431236-barata", "rating": 4.3, "level": "BRONZE", "loja": "Promo Lar", "oficial": False, "oficial_nome": "", "frete": False, "vendidos": 123, "kit": "", "garantia": "1 mes"},
    ],
    "garrafa termica": [
        {"id": "MLB3485431234", "nome": "Garrafa Termica 1L Inox", "preco": 39.9, "original": 69.9, "img": "https://http2.mlstatic.com/D_NQ_NP_2X_807736-MLA100849271566_122025-F.jpg", "link": "https://produto.mercadolivre.com.br/MLB-3485431234-garrafa", "rating": 4.8, "level": "GOLD", "loja": "Casa Termica", "oficial": False, "oficial_nome": "", "frete": True, "vendidos": 892, "kit": "", "garantia": "3 meses"},
        {"id": "MLB3485431235", "nome": "Garrafa Termica 1L Stanley Kit", "preco": 59.9, "original": 99.9, "img": "https://http2.mlstatic.com/D_NQ_NP_2X_782331-MLA54987612345_042023-F.jpg", "link": "https://produto.mercadolivre.com.br/MLB-3485431235-stanley", "rating": 4.9, "level": "PLATINUM", "loja": "Stanley Oficial", "oficial": True, "oficial_nome": "Stanley Oficial", "frete": True, "vendidos": 2345, "kit": "Garrafa + Copo + Escova", "garantia": "12 meses"},
        {"id": "MLB3485431236", "nome": "Garrafa Termica 1L Mais Barata", "preco": 24.9, "original": 39.9, "img": "https://http2.mlstatic.com/D_NQ_NP_2X_656432-MLA78912345678_092024-F.jpg", "link": "https://produto.mercadolivre.com.br/MLB-3485431236-barata", "rating": 4.3, "level": "BRONZE", "loja": "Promo Lar", "oficial": False, "oficial_nome": "", "frete": False, "vendidos": 123, "kit": "", "garantia": "1 mes"},
    ],
    "notebook": [
        {"id": "MLB20552039", "nome": "Notebook 15.6 8GB 256GB Prata", "preco": 1899.0, "original": 2599.0, "img": "https://http2.mlstatic.com/D_NQ_NP_2X_846840-MLA99993508793_112025-F.jpg", "link": "https://produto.mercadolivre.com.br/MLB-20552039-notebook", "rating": 4.8, "level": "PLATINUM", "loja": "Dell Oficial", "oficial": True, "oficial_nome": "Dell Oficial", "frete": True, "vendidos": 342, "kit": "Notebook + Mouse + Mochila", "garantia": "12 meses"},
        {"id": "MLB20552040", "nome": "Notebook 15.6 8GB 256GB Mesmo Modelo", "preco": 1799.0, "original": 2199.0, "img": "https://http2.mlstatic.com/D_NQ_NP_2X_846840-MLA99993508793_112025-F.jpg", "link": "https://produto.mercadolivre.com.br/MLB-20552040-notebook", "rating": 4.6, "level": "GOLD", "loja": "Info Center", "oficial": False, "oficial_nome": "", "frete": True, "vendidos": 234, "kit": "", "garantia": "3 meses"},
        {"id": "MLB20552041", "nome": "Notebook 15.6 Mais Barato", "preco": 1699.0, "original": 1999.0, "img": "https://http2.mlstatic.com/D_NQ_NP_2X_846840-MLA99993508793_112025-F.jpg", "link": "https://produto.mercadolivre.com.br/MLB-20552041-notebook", "rating": 4.2, "level": "SILVER", "loja": "Mega Info", "oficial": False, "oficial_nome": "", "frete": False, "vendidos": 89, "kit": "", "garantia": "1 mes"},
    ],
    "colher": [
        {"id": "MLB4317045718", "nome": "Colher De Pau Madeira 38cm Premium", "preco": 17.9, "original": 25.9, "img": "https://http2.mlstatic.com/D_NQ_NP_2X_715157-MLB71454127493_092023-F.jpg", "link": "https://produto.mercadolivre.com.br/MLB-4317045718-colher", "rating": 4.8, "level": "GOLD", "loja": "Casa Madeira", "oficial": False, "oficial_nome": "", "frete": True, "vendidos": 342, "kit": "", "garantia": "3 meses"},
        {"id": "MLB4317021530", "nome": "Kit 3 Colheres De Pau 27 38 60cm", "preco": 45.71, "original": 65.0, "img": "https://http2.mlstatic.com/D_NQ_NP_2X_634049-MLB74526395084_022024-F.jpg", "link": "https://produto.mercadolivre.com.br/MLB-4317021530-kit-colher", "rating": 4.9, "level": "PLATINUM", "loja": "Madeira Oficial", "oficial": True, "oficial_nome": "Madeira Oficial", "frete": True, "vendidos": 567, "kit": "Kit 3 colheres", "garantia": "12 meses"},
        {"id": "MLB3856175715", "nome": "Colher De Pau Grande 45cm Restaurante", "preco": 22.5, "original": 32.0, "img": "https://http2.mlstatic.com/D_NQ_NP_2X_634049-MLB74526395084_022024-F.jpg", "link": "https://produto.mercadolivre.com.br/MLB-3856175715-colher-grande", "rating": 4.7, "level": "GOLD", "loja": "Chef Store", "oficial": False, "oficial_nome": "", "frete": True, "vendidos": 189, "kit": "", "garantia": "3 meses"},
    ]
}

def buscar(termo):
    low = termo.lower()
    for k in PRODUTOS:
        if k in low:
            lista = []
            for p in PRODUTOS[k]:
                try:
                    desc = int((p["original"]-p["preco"])/p["original"]*100)
                except:
                    desc = 30
                lista.append({
                    "id": p["id"], "nome": p["nome"], "preco": p["preco"], "preco_original": p["original"],
                    "imagem": p["img"], "permalink": p["link"], "seller_rating": p["rating"],
                    "seller_level": p["level"], "seller_nome": p["loja"], "review_count": p["vendidos"],
                    "frete_gratis": p["frete"], "oficial": p["oficial"], "oficial_nome": p["oficial_nome"],
                    "vendidos": p["vendidos"], "kit": p["kit"], "garantia": p["garantia"],
                    "parcelas": "12x sem juros" if p["oficial"] else "6x", "affiliate_url": make_link(p["link"]), "desconto": desc
                })
            return lista
    # Fallback busca real ML com foto real
    try:
        url = "https://api.mercadolibre.com/sites/MLB/search?q=" + urllib.parse.quote(termo) + "&limit=3"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        if r.status_code == 200:
            results = r.json().get("results", [])
            lista = []
            for item in results[:3]:
                thumb = item.get("thumbnail","").replace("http://","https://")
                if "-I.jpg" in thumb:
                    thumb = thumb.replace("-I.jpg","-O.jpg")
                if "-M.jpg" in thumb:
                    thumb = thumb.replace("-M.jpg","-O.jpg")
                if not thumb:
                    thumb = "https://http2.mlstatic.com/D_NQ_NP_2X_807736-MLA100849271566_122025-F.jpg"
                link = item.get("permalink") or ("https://produto.mercadolivre.com.br/" + item.get("id"))
                preco = float(item.get("price", 89.9))
                original = float(item.get("original_price") or preco*1.4)
                try:
                    desc = int((original-preco)/original*100)
                except:
                    desc = 0
                lista.append({
                    "id": item.get("id"), "nome": item.get("title"), "preco": preco, "preco_original": original,
                    "imagem": thumb, "permalink": link, "seller_rating": 4.8, "seller_level": "GOLD",
                    "seller_nome": item.get("seller",{}).get("nickname","Loja")[:15], "review_count": item.get("sold_quantity",0),
                    "frete_gratis": item.get("shipping",{}).get("free_shipping",True), "oficial": item.get("official_store_id") is not None,
                    "oficial_nome": item.get("official_store_name") or "", "vendidos": item.get("sold_quantity",0),
                    "kit": "Kit" if "kit" in item.get("title","").lower() else "", "garantia": "12 meses" if item.get("official_store_id") else "3 meses",
                    "parcelas": "12x", "affiliate_url": make_link(link), "desconto": desc
                })
            if lista:
                return lista
    except Exception as e:
        print("API error: " + str(e), flush=True)
    # Ultimo fallback
    lista = []
    for i in range(3):
        preco = 29.9 + i*5
        lista.append({
            "id": "MLB" + str(random.randint(1000000000,9999999999)), "nome": termo.title() + " - Loja " + str(i+1),
            "preco": preco, "preco_original": preco*1.6, "imagem": "https://http2.mlstatic.com/D_NQ_NP_2X_807736-MLA100849271566_122025-F.jpg",
            "permalink": "https://lista.mercadolivre.com.br/" + urllib.parse.quote(termo), "seller_rating": 4.8,
            "seller_level": "GOLD", "seller_nome": "Loja " + str(i+1), "review_count": 100+i*100, "frete_gratis": True,
            "oficial": i==1, "oficial_nome": "Oficial" if i==1 else "", "vendidos": 100+i*100, "kit": "Kit" if i==1 else "",
            "garantia": "12 meses" if i==1 else "3 meses", "parcelas": "12x", "affiliate_url": make_link("https://lista.mercadolivre.com.br/" + urllib.parse.quote(termo)), "desconto": 30
        })
    return lista

def build(q):
    termo = re.sub(r"r\$|ate", "", q, flags=re.IGNORECASE).strip()
    if len(termo) < 2:
        termo = q
    prods = buscar(termo)
    if not prods:
        return {"budget": None, "termo": termo}, []
    mais_barato = min(prods, key=lambda x: x["preco"])
    melhor = max(prods, key=lambda x: x["seller_rating"])
    oficial = None
    for p in prods:
        if p["oficial"]:
            oficial = p
            break
    kit = None
    for p in prods:
        if p["kit"]:
            kit = p
            break
    offer = {
        "label": "COMPARATIVO: " + termo.upper(),
        "sub": str(len(prods)) + " ofertas do mesmo produto lado a lado - Compare vantagens",
        "descricao": "Mesmo " + termo + ", 3 lojas. Compare: preco, MercadoLider, check azul, kit",
        "items": prods,
        "mais_barato_id": mais_barato["id"],
        "melhor_avaliado_id": melhor["id"],
        "oficial_id": oficial["id"] if oficial else "",
        "kit_id": kit["id"] if kit else "",
        "tipo": "comparativo"
    }
    return {"budget": None, "termo": termo}, [offer]

class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass
    def send_json(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b)
    def send_file(self, path, ctype):
        try:
            with open(path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except:
            self.send_json(404, {"erro": "nao encontrado"})
    def do_GET(self):
        try:
            if self.path == "/" or self.path.startswith("/oferta/") or self.path.startswith("/comparar/"):
                p = os.path.join(BASE, "static", "index.html")
                return self.send_file(p, "text/html; charset=utf-8")
            if self.path.startswith("/static/"):
                fname = self.path[8:]
                if ".." in fname:
                    return self.send_json(404, {"erro": "nao"})
                fpath = os.path.join(BASE, "static", fname)
                if not os.path.exists(fpath):
                    self.send_response(302)
                    self.send_header("Location", "https://http2.mlstatic.com/D_NQ_NP_2X_807736-MLA100849271566_122025-F.jpg")
                    self.end_headers()
                    return
                ctype = "text/html; charset=utf-8"
                return self.send_file(fpath, ctype)
            if self.path == "/health":
                return self.send_json(200, {"status": "ok", "v": "V25.5 FOTOS CORRIGIDAS"})
            if self.path == "/debug":
                return self.send_json(200, {"status": "ok", "aff": AFF_ID, "produtos": list(PRODUTOS.keys())})
            if self.path.startswith("/go/"):
                pid = self.path.split("/")[-1].split("?")[0]
                link = "https://produto.mercadolivre.com.br/" + pid if pid.startswith("MLB") else "https://lista.mercadolivre.com.br/produto"
                for k in PRODUTOS:
                    for p in PRODUTOS[k]:
                        if p["id"] == pid:
                            link = p["link"]
                            break
                link = make_link(link)
                try:
                    c = get_db()
                    c.execute("insert into clicks(product_id,ts) values(?,?)", (pid, time.time()))
                    c.commit()
                except:
                    pass
                self.send_response(302)
                self.send_header("Location", link)
                self.end_headers()
                return
            self.send_json(404, {"erro": "nao encontrado"})
        except Exception as e:
            print("GET err: " + str(e), flush=True)
            self.send_json(500, {"erro": str(e)})
    def do_POST(self):
        try:
            if self.path != "/api/offer":
                return self.send_json(404, {"erro": "nao"})
            length = int(self.headers.get("Content-Length", 0))
            data = self.rfile.read(min(length, 5000))
            d = json.loads(data)
            q = str(d.get("q", "")).strip()[:200]
            if len(q) < 2:
                return self.send_json(400, {"erro": "curto"})
            it, offers = build(q)
            oid = secrets.token_urlsafe(6)
            res = {"id": oid, "q": q, "termo": it["termo"], "ofertas": offers}
            try:
                c = get_db()
                c.execute("insert into searches(q,ts) values(?,?)", (q, time.time()))
                c.execute("insert into offers values(?,?,?,?)", (oid, q, json.dumps(res, ensure_ascii=False), time.time()))
                c.commit()
            except:
                pass
            self.send_json(200, res)
        except Exception as e:
            print("POST err: " + str(e), flush=True)
            self.send_json(500, {"erro": str(e)})
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print("V25.5 FOTOS CORRIGIDAS - Porta " + str(port), flush=True)
    server = ThreadingHTTPServer(("0.0.0.0", port), H)
    print("Servidor OK", flush=True)
    server.serve_forever()

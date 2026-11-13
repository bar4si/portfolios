"""Gera as revistas HTML dos portfolios e a pagina-indice do site.

Uso:
    python gerar.py resiliencia-organica    gera so esse portfolio (e o indice)
    python gerar.py                         gera todos (e o indice)

Cada portfolio e uma pasta com:
    textos.json     textos e sequencia de paginas
    images/         as fotos (N.jpg), com os nomes usados em "fotos" no textos.json
    modelo.html     o visual da revista (cada portfolio tem o seu)

O resultado sai em <pasta>/index.html, com as fotos embutidas, e em index.html
na raiz, que lista todos os portfolios (visual em modelo-indice.html).
Publicado no GitHub Pages, cada portfolio abre em .../<pasta>/.
"""
import base64, html, io, json, os, sys
from PIL import Image, ImageOps

RAIZ = os.path.dirname(os.path.abspath(__file__))
ALTURA_MAX = 2160
ALTURA_CAPA = 1200
MARCA = "/*__IMGS__*/"
MARCA_CARTOES = "<!--__CARTOES__-->"
MARCA_AUTOR = "<!--__AUTOR__-->"


def ler(caminho):
    with open(caminho, encoding="utf-8") as f:
        return f.read()


def gravar(caminho, conteudo):
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)


def foto(pasta, chave, altura, qualidade=82):
    """Le images/<chave>.jpg, reduz para a altura dada e devolve como data URI."""
    im = ImageOps.exif_transpose(Image.open(os.path.join(pasta, "images", f"{chave}.jpg"))).convert("RGB")
    if im.height > altura:
        im = im.resize((round(im.width * altura / im.height), altura), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=qualidade, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def portfolios():
    return sorted(d for d in os.listdir(RAIZ) if os.path.exists(os.path.join(RAIZ, d, "textos.json")))


def gerar(nome):
    pasta = os.path.join(RAIZ, nome)
    textos = json.loads(ler(os.path.join(pasta, "textos.json")))
    modelo = ler(os.path.join(pasta, "modelo.html"))
    assert MARCA in modelo, "modelo.html sem o marcador " + MARCA

    fotos = {chave: foto(pasta, chave, ALTURA_MAX) for chave in textos["fotos"]}
    dados = ("const IMG=" + json.dumps(fotos) + ";\nconst T="
             + json.dumps(textos, ensure_ascii=False).replace("</", "<" + chr(92) + "/") + ";")
    saida = os.path.join(pasta, "index.html")
    gravar(saida, modelo.replace(MARCA, dados))
    print(f"{nome}/index.html gerada ({os.path.getsize(saida) / 1e6:.1f} MB, {len(fotos)} fotos)")


def gerar_indice():
    modelo = ler(os.path.join(RAIZ, "modelo-indice.html"))
    for marca in (MARCA_CARTOES, MARCA_AUTOR):
        assert marca in modelo, "modelo-indice.html sem o marcador " + marca

    e = html.escape
    cartoes, autores = [], []
    for nome in portfolios():
        pasta = os.path.join(RAIZ, nome)
        if not os.path.exists(os.path.join(pasta, "index.html")):
            continue  # ainda nao gerado
        t = json.loads(ler(os.path.join(pasta, "textos.json")))
        capa = t["capa"]
        if capa["autor"] not in autores:
            autores.append(capa["autor"])
        cartoes.append(
            f'<a class="cartao" href="{e(nome)}/">'
            f'<figure><img src="{foto(pasta, capa["foto"], ALTURA_CAPA, 80)}" alt="Capa de {e(t["titulo"])} {e(t["titulo_italico"])}"></figure>'
            f'<div class="lab">{e(capa["chamada"])}</div>'
            f'<h2>{e(t["titulo"])} <em>{e(t["titulo_italico"])}</em></h2>'
            f'<p>{e(t["subtitulo"])}</p></a>')

    saida = os.path.join(RAIZ, "index.html")
    gravar(saida, modelo.replace(MARCA_CARTOES, "\n".join(cartoes)).replace(MARCA_AUTOR, e(" · ".join(autores))))
    print(f"index.html gerado ({os.path.getsize(saida) / 1e6:.1f} MB, {len(cartoes)} portfolio(s))")


if __name__ == "__main__":
    nomes = [a.strip("/\\") for a in sys.argv[1:]] or portfolios()
    if not nomes:
        sys.exit("Nenhum portfolio encontrado (pasta com textos.json).")
    for n in nomes:
        gerar(n)
    gerar_indice()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成「肥猫商城 Hot_Mall 详细设计说明（扩展版）」Word 文档（Office Open XML .docx）。
仅依赖 Python 标准库；在项目根目录执行:
  python3 scripts/generate_design_docx.py
输出: docs/Hot_Mall_详细设计说明_扩展.docx
.doc 为 Word 97-2003 二进制格式，本脚本生成 OOXML .docx（Word 可直接打开，另存为可得 .doc）。
"""
import os
import sys
import zipfile
from xml.sax.saxutils import escape


def w_p(text, bold=False, mono=False):
    text = escape(text.replace("\r", ""))
    rpr = ""
    if bold:
        rpr += "<w:b/>"
    if mono:
        rpr += (
            '<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:eastAsia="SimSun"/>'
            '<w:sz w:val="20"/><w:szCs w:val="20"/>'
        )
    r_inner = ("<w:rPr>%s</w:rPr>" % rpr) if rpr else ""
    return (
        "<w:p>"
        "<w:pPr><w:spacing w:before=\"60\" w:after=\"60\"/></w:pPr>"
        "<w:r>%s<w:t xml:space=\"preserve\">%s</w:t></w:r>"
        "</w:p>" % (r_inner, text)
    )


def w_title(text):
    return (
        "<w:p>"
        "<w:pPr><w:pStyle w:val=\"Title\"/><w:jc w:val=\"center\"/></w:pPr>"
        "<w:r><w:rPr><w:b/><w:sz w:val=\"36\"/></w:rPr>"
        "<w:t xml:space=\"preserve\">%s</w:t></w:r>"
        "</w:p>" % escape(text)
    )


def w_h1(text):
    return (
        "<w:p><w:pPr><w:pStyle w:val=\"Heading1\"/></w:pPr>"
        "<w:r><w:rPr><w:b/><w:sz w:val=\"32\"/></w:rPr>"
        "<w:t xml:space=\"preserve\">%s</w:t></w:r></w:p>" % escape(text)
    )


def w_h2(text):
    return (
        "<w:p><w:pPr><w:pStyle w:val=\"Heading2\"/></w:pPr>"
        "<w:r><w:rPr><w:b/><w:sz w:val=\"28\"/></w:rPr>"
        "<w:t xml:space=\"preserve\">%s</w:t></w:r></w:p>" % escape(text)
    )


def build_document_xml():
    parts = []
    parts.append(
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>"
    )
    parts.append(w_title("肥猫商城（Hot_Mall）详细设计说明（扩展版）"))
    parts.append(w_p("文档生成：自动生成脚本 scripts/generate_design_docx.py", mono=True))
    parts.append(
        w_p(
            "格式说明：本文件为 Office Open XML 格式，扩展名 .docx。Microsoft Word 可直接打开。"
            "若需传统 .doc（Word 97-2003），请在 Word 中使用「另存为」选择「Word 97-2003 文档(*.doc)」。"
        )
    )
    parts.append(w_h1("1. 文档范围与配套文件"))
    parts.append(
        w_p(
            "本扩展版在根目录 DESIGN.md 概要设计基础上，补充：用例/类图/时序图（Mermaid 源码）、"
            "OpenAPI 3.0 风格接口清单（YAML），并汇总于本文档便于评审与归档。"
        )
    )
    parts.append(w_p("配套文件路径：", bold=True))
    parts.append(w_p("• docs/openapi.yaml — 接口清单（OpenAPI 3.0.3）", mono=True))
    parts.append(w_p("• docs/design_diagrams_mermaid.md — UML/用例/时序 Mermaid 图源", mono=True))
    parts.append(w_p("• DESIGN.md — 项目总体详细设计（Markdown）", mono=True))

    parts.append(w_h1("2. 系统用例（文字说明 + Mermaid）"))
    parts.append(
        w_p(
            "主要参与者：访客、注册用户、运营人员。访客可浏览与搜索；注册用户完成账号、地址、购物车、"
            "下单与支付、订单评价；运营维护 SKU、图片、条码检索及临期商品；采购维护供应商与进货记录。"
        )
    )
    parts.append(w_p("用例图 Mermaid（可复制到 mermaid.live 渲染）：", bold=True))
    mermaid_uc = """flowchart LR
  subgraph 访客
    UC1[浏览首页/商品]
    UC2[搜索商品]
  end
  subgraph 注册用户
    UC3[注册/登录]
    UC4[维护地址]
    UC5[购物车]
    UC6[下单支付]
    UC7[订单/评价]
  end
  subgraph 运营
    UC8[商品 SKU 管理]
    UC9[供应商/进货]
  end
  HotMall((肥猫商城))
  UC1 --> HotMall
  UC2 --> HotMall
  UC3 --> HotMall
  UC4 --> HotMall
  UC5 --> HotMall
  UC6 --> HotMall
  UC7 --> HotMall
  UC8 --> HotMall
  UC9 --> HotMall"""
    for line in mermaid_uc.split("\n"):
        parts.append(w_p(line, mono=True))

    parts.append(w_h1("3. 核心域类图（简化 UML）"))
    parts.append(w_p("核心实体：User、Address、SKU/SPU、OrderInfo、OrderGoods、Payment、Supplier、SupplierPurchaseRecord（表 tb_supplier_purchase）。"))
    parts.append(w_p("类图 Mermaid：", bold=True))
    mermaid_class = """classDiagram
  class User
  class Address
  class SKU
  class OrderInfo
  class OrderGoods
  class Supplier
  class SupplierPurchaseRecord
  User "1" --> "*" Address
  User "1" --> "*" OrderInfo
  OrderInfo "1" --> "*" OrderGoods
  OrderGoods "*" --> "1" SKU
  Supplier "1" --> "*" SupplierPurchaseRecord"""
    for line in mermaid_class.split("\n"):
        parts.append(w_p(line, mono=True))

    parts.append(w_h1("4. 时序图"))
    parts.append(w_h2("4.1 提交订单与乐观锁库存"))
    parts.append(w_p("浏览器 POST /orders/commit/ → 读 Redis 购物车 → 事务内按 SKU 乐观锁扣减库存 → 写订单 → 清理 Redis。"))
    mermaid_seq1 = """sequenceDiagram
  participant B as 浏览器
  participant O as OrderCommitView
  participant R as Redis
  participant DB as MySQL
  B->>O: POST JSON
  O->>R: 读取选中 SKU
  O->>DB: 事务+乐观锁更新 stock
  O-->>B: order_id / 错误码"""
    for line in mermaid_seq1.split("\n"):
        parts.append(w_p(line, mono=True))

    parts.append(w_h2("4.2 支付宝支付"))
    mermaid_seq2 = """sequenceDiagram
  participant B as 浏览器
  participant P as PaymentView
  participant A as 支付宝
  B->>P: GET /payment/{order_id}/
  P-->>B: alipay_url
  B->>A: 跳转支付
  A-->>B: return_url 回调"""
    for line in mermaid_seq2.split("\n"):
        parts.append(w_p(line, mono=True))

    parts.append(w_h1("5. 接口清单（OpenAPI 摘要）"))
    parts.append(
        w_p(
            "完整路径、参数与响应结构见 docs/openapi.yaml。以下为高频 JSON 接口列表（节选）："
        )
    )
    apis = [
        "GET /usernames/{username}/count/ — 用户名重复校验",
        "GET /mobiles/{mobile}/count/ — 手机号重复校验",
        "GET /sms_codes/{mobile}/ — 发短信（需 image_code、uuid）",
        "GET /image_codes/{uuid}/ — 图形验证码 JPEG",
        "GET|POST|PUT|DELETE /carts/ — 购物车 CRUD",
        "PUT /carts/selection/ — 全选/取消全选",
        "GET /carts/simple/ — 头部简单购物车",
        "POST /orders/commit/ — 提交订单（JSON：address_id, pay_method）",
        "GET /payment/{order_id}/ — 发起支付（支付宝 alipay_url / 微信 wechat_pay_url）",
        "GET /api/skus/ — 后台 SKU JSON 列表",
    ]
    for a in apis:
        parts.append(w_p("• " + a))

    parts.append(w_h1("6. 技术栈与部署要点（摘要）"))
    parts.append(w_p("Django 3.2 + MySQL + Redis（多库别名）+ Jinja2 + Haystack(Whoosh) + Celery；支付对接支付宝与微信 APIv3（含演示模式）。"))
    parts.append(w_p("生产环境务必关闭 DEBUG，使用环境变量管理密钥，并对支付回调 URL 使用 HTTPS 公网地址。"))

    parts.append(
        "<w:sectPr>"
        '<w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/>'
        "</w:sectPr>"
    )
    parts.append("</w:body></w:document>")
    return "".join(parts)


def build_styles_xml():
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:docDefaults><w:rPrDefault><w:rPr/></w:rPrDefault><w:pPrDefault><w:pPr/></w:pPrDefault></w:docDefaults>'
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
        '<w:name w:val="Normal"/><w:qFormat/>'
        "</w:style>"
        '<w:style w:type="paragraph" w:styleId="Title">'
        '<w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="240" w:after="120"/></w:pPr>'
        '<w:rPr><w:b/><w:sz w:val="36"/></w:rPr>'
        "</w:style>"
        '<w:style w:type="paragraph" w:styleId="Heading1">'
        '<w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
        '<w:pPr><w:keepNext/><w:spacing w:before="360" w:after="120"/></w:pPr>'
        '<w:rPr><w:b/><w:sz w:val="32"/></w:rPr>'
        "</w:style>"
        '<w:style w:type="paragraph" w:styleId="Heading2">'
        '<w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
        '<w:pPr><w:keepNext/><w:spacing w:before="280" w:after="100"/></w:pPr>'
        '<w:rPr><w:b/><w:sz w:val="28"/></w:rPr>'
        "</w:style>"
        "</w:styles>"
    )


def build_content_types():
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        "</Types>"
    )


def build_root_rels():
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )


def build_document_rels():
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        "</Relationships>"
    )


def write_docx(path):
    doc_xml = build_document_xml()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", build_content_types())
        z.writestr("_rels/.rels", build_root_rels())
        z.writestr("word/document.xml", doc_xml.encode("utf-8"))
        z.writestr("word/_rels/document.xml.rels", build_document_rels())
        z.writestr("word/styles.xml", build_styles_xml())


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(root, "docs")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "backup/Hot_Mall_详细设计说明_扩展.docx")
    write_docx(out)
    print("Written:", out)


if __name__ == "__main__":
    main()

import hashlib
from datetime import datetime

VULN_DB = {
    "BIM_Designer": {
        "v24.1": {
            "cve": "CVE-CON-001", 
            "title": "Утечка памяти при загрузке 3D-моделей свыше 2ГБ", 
            "severity": 8.5
        },
        "v23.5": {
            "cve": "CVE-CON-042", 
            "title": "Удаленное выполнение кода через макросы чертежей", 
            "severity": 9.8
        }
    },
    "Site_Access_Controller": {
        "firmware_1.0": {
            "cve": "CVE-SITE-10", 
            "title": "Обход аутентификации по мастер-ключу", 
            "severity": 10.0
        }
    },
    "Windows_Workstation": {
        "10_Enterprise_1909": {
            "cve": "CVE-WIN-202", 
            "title": "Повышение привилегий через службу печати", 
            "severity": 7.0
        }
    }
}

BUSINESS_CRITICALITY = {
    "BIM_Server": 10.0,           
    "Site_Gate_Controller": 9.5,  
    "QA_Engineer_PC": 4.0,        
    "HR_Workstation": 2.0      
}

ASSETS = [
    {
        "id": "AST-001",
        "name": "SRV-BIM-01",
        "type": "BIM_Server",
        "os": "Windows Server 2019",
        "software": {"BIM_Designer": "v23.5", "Backup_Agent": "v5.0"}
    },
    {
        "id": "AST-002",
        "name": "Gate-Main-Construction",
        "type": "Site_Gate_Controller",
        "os": "Embedded Linux",
        "software": {"Site_Access_Controller": "firmware_1.0"}
    },
    {
        "id": "AST-003",
        "name": "WK-IVANOV-QA",
        "type": "QA_Engineer_PC",
        "os": "Windows 10 Enterprise 1909",
        "software": {"BIM_Designer": "v24.1", "PDF_Reader": "v2020"}
    },
    {
        "id": "AST-004",
        "name": "WK-HR-01",
        "type": "HR_Workstation",
        "os": "Windows 11 Pro",
        "software": {"1C": "v8.3"}
    }
]

def calculate_risk(tech_severity, business_crit):

    return (tech_severity * 0.6) + (business_crit * 0.4)

def audit_assets(asset_list):
    findings = []
    
    for asset in asset_list:
        asset_risk = 0.0
        asset_vulns = []

        business_crit = BUSINESS_CRITICALITY.get(asset["type"], 5.0)
        
        for soft_name, version in asset["software"].items():
            if soft_name in VULN_DB and version in VULN_DB[soft_name]:
                vuln = VULN_DB[soft_name][version]

                risk_score = calculate_risk(vuln["severity"], business_crit)
                
                finding = {
                    "asset_id": asset["id"],
                    "asset_name": asset["name"],
                    "cve": vuln["cve"],
                    "title": vuln["title"],
                    "tech_severity": vuln["severity"],
                    "business_criticality": business_crit,
                    "risk_score": round(risk_score, 2),
                    "status": "OPEN"
                }
                
                asset_vulns.append(finding)
                asset_risk += risk_score

        asset_vulns.sort(key=lambda x: x["risk_score"], reverse=True)
        
        findings.append({
            "asset": asset,
            "total_risk": round(asset_risk, 2),
            "vulnerabilities": asset_vulns
        })
 
    findings.sort(key=lambda x: x["total_risk"], reverse=True)
    return findings

def generate_protocre_report(findings):
    """Этап 2: Формирование отчета и плана устранения"""
    
    print("\n" + "="*80)
    print("PROTOCRE: ОТЧЕТ АНАЛИЗА УЯЗВИМОСТЕЙ СТРОИТЕЛЬНОЙ КОМПАНИИ")
    print("="*80)
    
    total_company_risk = sum(f["total_risk"] for f in findings)
    print(f"ОБЩИЙ ИНДЕКС КРИТИЧНОСТИ КОМПАНИИ: {total_company_risk:.2f} / 100.00\n")

    print("ПЛАН УСТРАНЕНИЯ (REMEDIATION PLAN):")
    print("-" * 80)
    
    for item in findings:
        asset = item["asset"]
        print(f"\n[УЗЕЛ: {asset['name']} | ТИП: {asset['type']}]")
        print(f"Общий риск узла: {item['total_risk']:.2f}")
        
        if not item["vulnerabilities"]:
            print("  -> Статус: CLEAN (Уязвимостей не обнаружено)")
            continue
            
        for v in item["vulnerabilities"]:
            print(f"  -> [ID: {v['cve']}] {v['title']}")
            print(f"     Приоритет: {'КРИТИЧЕСКИЙ' if v['risk_score'] > 8.0 else 'ВЫСОКИЙ'}")
            print(f"     Рекомендация: Обновить {v['asset_name']} -> изолировать от внешней сети до патча.")

    report_string = str(findings) + str(datetime.now().date())
    integrity_hash = hashlib.sha256(report_string.encode()).hexdigest()
    
    print("\n" + "="*80)
    print("КОНТРОЛЬ ЦЕЛОСТНОСТИ ДАННЫХ")
    print("="*80)
    print(f"Хэш-сумма (SHA-256) аналитического среза: {integrity_hash}")
    print("Для фиксации состояния аудита в пояснительной записке курсовой работы.")
    print("="*80)

if __name__ == "__main__":

    scan_results = audit_assets(ASSETS)

    generate_protocre_report(scan_results)
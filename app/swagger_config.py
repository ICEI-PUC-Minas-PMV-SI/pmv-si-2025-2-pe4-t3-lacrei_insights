swagger_template = {
    "swagger": "2.0",
    "basePath": "/",  # rota base da API
    "schemes": ["http"],
    "consumes": [
        "application/json",
        "multipart/form-data"
    ],
    "produces": [
        "application/json"
    ],
    "tags": [
        {
            "name": "ETL",
            "description": "Processamento de dados staging 1 para staging 2"
        },
        {
            "name": "Upload no Power BI",
            "description": "Execução de rotinas e cargas no Data Warehouse"
        }
    ]
}

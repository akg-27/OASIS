backend/
│── app/
│   ├── main.py                      # App entry point
│   ├── config.py                    # Config & environment variables
│   ├── database.py                  # PostgreSQL connection + ORM
│   ├── routers/                     # All API Routes
│   │   ├── auth_routes.py
│   │   ├── upload_routes.py
│   │   ├── metadata_routes.py
│   │   ├── visualization_routes.py
│   │   ├── ai_otolith_routes.py
│   │   ├── ai_taxonomy_routes.py
│   │   └── ai_edna_routes.py
│   ├── services/                    # Business Logic & Processing
│   │   ├── ingestion_service.py
│   │   ├── metadata_service.py
│   │   ├── preprocessing_service.py
│   │   ├── visualization_service.py
│   │   ├── otolith_service.py
│   │   ├── taxonomy_service.py
│   │   └── edna_service.py
│   ├── models/                      # Database Models (SQLAlchemy)
│   │   ├── user_model.py
│   │   ├── metadata_model.py
│   │   ├── taxonomy_model.py
│   │   ├── otolith_model.py
│   │   └── edna_model.py
│   ├── schemas/                     # Request/Response Validation (Pydantic)
│   │   ├── user_schema.py
│   │   ├── metadata_schema.py
│   │   └── dataset_schema.py
│   ├── utils/                       # Helpers & Constants
│   │   ├── file_storage.py
│   │   ├── constants.py
│   │   └── helpers.py
│   ├── ml/                           # Trained Model Files
│   │   ├── otolith_model.pkl
│   │   ├── taxonomy_cnn.pt
│   │   └── dna_reference.json
│── requirements.txt
│── README.md
|-uploads
|-.env



🔐 Authentication (auth_routes.py)
| Method | Endpoint         | Description       |
| ------ | ---------------- | ----------------- |
| POST   | `/auth/register` | User registration |
| POST   | `/auth/login`    | Login & token     |


📤 Dataset Upload (upload_routes.py)
| Method | Endpoint           | Upload Type                       |
| ------ | ------------------ | --------------------------------- |
| POST   | `/upload/ocean`    | Oceanographic dataset (CSV/Excel) |
| POST   | `/upload/taxonomy` | Fish taxonomy dataset             |
| POST   | `/upload/otolith`  | Otolith image                     |
| POST   | `/upload/edna`     | DNA sequence file/text            |


🏷️ Metadata & Approval (metadata_routes.py)
| Method | Endpoint                 | Purpose                   |
| ------ | ------------------------ | ------------------------- |
| GET    | `/metadata/list`         | List datasets with status |
| GET    | `/metadata/{id}`         | View metadata details     |
| PUT    | `/metadata/approve/{id}` | Approve dataset           |
| PUT    | `/metadata/reject/{id}`  | Reject dataset            |


📊 Visualization (visualization_routes.py)
| Method | Endpoint             | Purpose                         |
| ------ | -------------------- | ------------------------------- |
| GET    | `/visualize/ocean`   | Plot salinity/temp/depth trends |
| GET    | `/visualize/species` | Species abundance trends        |
| GET    | `/visualize/map`     | Species distribution on map     |


🧠 Otolith AI (ai_otolith_routes.py)
| Method | Endpoint              | Purpose                                     |
| ------ | --------------------- | ------------------------------------------- |
| POST   | `/ai/otolith/analyze` | Upload otolith, get prediction + similarity |


🐟 Taxonomy AI (ai_taxonomy_routes.py)
| Method | Endpoint                | Purpose                             |
| ------ | ----------------------- | ----------------------------------- |
| POST   | `/ai/taxonomy/classify` | Upload fish image → species predict |
| GET    | `/ai/taxonomy/info`     | Fetch taxonomy traits               |


🧬 eDNA Identification (ai_edna_routes.py)
| Method | Endpoint           | Purpose                      |
| ------ | ------------------ | ---------------------------- |
| POST   | `/ai/edna/match`   | Upload DNA sequence → match  |
| GET    | `/ai/edna/history` | Previous sequence detections |
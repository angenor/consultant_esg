# 05 - API Endpoints

## Vue d'ensemble des routes

```
/api
├── /auth
│   ├── POST   /register          → Inscription
│   ├── POST   /login             → Connexion (retourne JWT)
│   └── GET    /me                → Profil utilisateur connecté
│
├── /entreprises
│   ├── POST   /                  → Créer une entreprise
│   ├── GET    /                  → Lister mes entreprises
│   ├── GET    /{id}              → Détail d'une entreprise
│   ├── PUT    /{id}              → Modifier une entreprise
│   └── GET    /{id}/scores       → Historique des scores ESG
│
├── /chat
│   ├── POST   /conversations                      → Nouvelle conversation
│   ├── GET    /conversations                       → Lister mes conversations
│   ├── GET    /conversations/{id}                  → Historique d'une conversation
│   ├── POST   /conversations/{id}/message          → Envoyer message (SSE stream)
│   ├── POST   /conversations/{id}/audio            → Envoyer message vocal (STT → texte → agent)
│   └── DELETE /conversations/{id}                  → Supprimer conversation
│
├── /documents
│   ├── POST   /upload                              → Upload document
│   ├── GET    /entreprise/{id}                     → Lister documents d'une entreprise
│   ├── GET    /{id}                                → Détail d'un document
│   └── DELETE /{id}                                → Supprimer un document
│
├── /reports
│   ├── POST   /generate                            → Générer un rapport PDF
│   ├── GET    /entreprise/{id}                     → Lister rapports d'une entreprise
│   └── GET    /{id}/download                       → Télécharger un rapport PDF
│
├── /carbon
│   ├── GET    /entreprise/{id}                     → Historique empreinte carbone
│   └── GET    /entreprise/{id}/evolution            → Évolution mensuelle/annuelle
│
├── /credit-score
│   ├── POST   /calculate                            → Calculer score crédit vert
│   ├── GET    /entreprise/{id}                     → Dernier score + historique
│   └── POST   /entreprise/{id}/share                → Générer lien de partage sécurisé (token temporaire)
│
├── /action-plans
│   ├── POST   /                                     → Créer un plan d'action
│   ├── GET    /entreprise/{id}                     → Plans de l'entreprise
│   ├── GET    /{id}                                 → Détail d'un plan avec ses actions
│   ├── PUT    /items/{item_id}                      → Mettre à jour statut d'une action
│   └── GET    /{id}/progress                        → Progression globale du plan
│
├── /notifications
│   ├── GET    /                                     → Mes notifications
│   ├── PUT    /{id}/read                            → Marquer comme lue
│   └── GET    /unread-count                         → Compteur non lues
│
├── /benchmark
│   └── GET    /secteur/{secteur}                    → Moyennes sectorielles ESG + carbone
│
├── /admin  (role = admin requis)
│   ├── /skills
│   │   ├── GET    /                                → Lister tous les skills
│   │   ├── POST   /                                → Créer un skill
│   │   ├── GET    /{id}                            → Détail d'un skill
│   │   ├── PUT    /{id}                            → Modifier un skill
│   │   ├── DELETE /{id}                            → Supprimer un skill
│   │   ├── POST   /{id}/toggle                     → Activer/désactiver
│   │   └── POST   /{id}/test                       → Tester un skill
│   │
│   ├── /referentiels
│   │   ├── GET    /                                → Lister les référentiels ESG
│   │   ├── POST   /                                → Créer un référentiel
│   │   ├── GET    /{id}                            → Détail (avec grille complète)
│   │   ├── PUT    /{id}                            → Modifier un référentiel
│   │   ├── DELETE /{id}                            → Supprimer un référentiel
│   │   ├── POST   /{id}/toggle                     → Activer/désactiver
│   │   └── POST   /{id}/preview                    → Simuler un scoring avec données test
│   │
│   ├── /fonds
│   │   ├── GET    /                                → Lister les fonds verts
│   │   ├── POST   /                                → Ajouter un fonds (+ lien référentiel)
│   │   ├── PUT    /{id}                            → Modifier un fonds
│   │   └── DELETE /{id}                            → Supprimer un fonds
│   │
│   ├── /templates
│   │   ├── GET    /                                → Lister templates de rapports
│   │   ├── POST   /                                → Créer un template
│   │   ├── PUT    /{id}                            → Modifier un template
│   │   └── POST   /{id}/preview                    → Prévisualiser un template
│   │
│   └── /stats
│       └── GET    /dashboard                       → Statistiques globales
```

## Détail des Endpoints Principaux

### Auth

```python
# === backend/app/api/auth.py ===

router = APIRouter(prefix="/api/auth", tags=["auth"])

# --- Schemas ---
class RegisterRequest(BaseModel):
    email: str
    password: str
    nom_complet: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# --- Endpoints ---
@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, db=Depends(get_db)):
    """Inscription. Crée le user + retourne un JWT."""

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db=Depends(get_db)):
    """Connexion par email/password. Retourne un JWT."""

@router.get("/me", response_model=UserResponse)
async def get_me(user=Depends(get_current_user)):
    """Retourne le profil de l'utilisateur connecté."""
```

### Chat (endpoint principal)

```python
# === backend/app/api/chat.py ===

router = APIRouter(prefix="/api/chat", tags=["chat"])

# --- Schemas ---
class CreateConversationRequest(BaseModel):
    entreprise_id: str
    titre: str | None = None

class SendMessageRequest(BaseModel):
    message: str

# --- Endpoints ---
@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    body: CreateConversationRequest,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Crée une nouvelle conversation liée à une entreprise."""

@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Liste les conversations de l'utilisateur."""

@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Récupère l'historique complet d'une conversation."""

@router.post("/conversations/{conversation_id}/message")
async def send_message(
    conversation_id: str,
    body: SendMessageRequest,
    user=Depends(get_current_user),
    db=Depends(get_db),
    agent=Depends(get_agent_engine),
):
    """
    Envoie un message et stream la réponse via SSE.

    Events SSE :
    - event: text          → Texte de la réponse (streaming mot par mot)
    - event: skill_start   → Un skill commence (nom + params)
    - event: skill_result  → Un skill a fini (résumé du résultat)
    - event: done          → Fin de la réponse
    - event: error         → Erreur
    """
    async def event_generator():
        try:
            async for event in agent.run(
                conversation_id=conversation_id,
                user_message=body.message,
                entreprise=await get_entreprise_for_conversation(conversation_id, db),
            ):
                yield {"event": event["type"], "data": json.dumps(event)}
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator())
```

### Documents

```python
# === backend/app/api/documents.py ===

router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile,
    entreprise_id: str = Form(...),
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Upload un document (PDF, image, Word, Excel).
    1. Sauvegarde le fichier
    2. Extrait le texte (OCR si nécessaire)
    3. Crée les chunks + embeddings pour le RAG
    """
    # Validation
    allowed = ["application/pdf", "image/png", "image/jpeg",
               "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]
    if file.content_type not in allowed:
        raise HTTPException(400, f"Type non supporté: {file.content_type}")

    # Sauvegarder le fichier
    file_path = await save_uploaded_file(file, entreprise_id)

    # Extraire le texte
    text = await extract_text_from_file(file_path, file.content_type)

    # Sauvegarder en BDD
    doc = await db.execute(
        """INSERT INTO documents (entreprise_id, nom_fichier, type_mime, chemin_stockage, taille, texte_extrait)
           VALUES ($1, $2, $3, $4, $5, $6) RETURNING *""",
        entreprise_id, file.filename, file.content_type, file_path, file.size, text
    )

    # Créer les chunks + embeddings (en arrière-plan pour le MVP synchrone)
    await create_document_chunks(doc["id"], text, db)

    return doc
```

### Admin - Skills

```python
# === backend/app/api/admin/skills.py ===

router = APIRouter(prefix="/api/admin/skills", tags=["admin-skills"])

# --- Schemas ---
class SkillCreateRequest(BaseModel):
    nom: str
    description: str
    category: str
    input_schema: dict    # JSON Schema
    handler_key: str      # "builtin.xxx" ou "custom.xxx"
    handler_code: str | None = None  # Code Python pour les customs

class SkillUpdateRequest(BaseModel):
    description: str | None = None
    input_schema: dict | None = None
    handler_code: str | None = None
    is_active: bool | None = None

class SkillTestRequest(BaseModel):
    params: dict          # Paramètres de test

# --- Endpoints ---
@router.get("/", response_model=list[SkillResponse])
async def list_skills(
    category: str | None = None,
    admin=Depends(require_admin),
    db=Depends(get_db),
):
    """Liste tous les skills (actifs et inactifs)."""

@router.post("/", response_model=SkillResponse)
async def create_skill(
    body: SkillCreateRequest,
    admin=Depends(require_admin),
    db=Depends(get_db),
):
    """
    Crée un nouveau skill.
    Si handler_key commence par "custom.", valide le handler_code.
    """
    if body.handler_key.startswith("custom.") and body.handler_code:
        valid, error = validate_skill_code(body.handler_code)
        if not valid:
            raise HTTPException(400, f"Code invalide : {error}")

    return await db.execute(
        """INSERT INTO skills (nom, description, category, input_schema, handler_key, handler_code, created_by)
           VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING *""",
        body.nom, body.description, body.category,
        json.dumps(body.input_schema), body.handler_key,
        body.handler_code, admin["id"],
    )

@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    body: SkillUpdateRequest,
    admin=Depends(require_admin),
    db=Depends(get_db),
):
    """Modifie un skill existant. Incrémente la version."""
    if body.handler_code:
        valid, error = validate_skill_code(body.handler_code)
        if not valid:
            raise HTTPException(400, f"Code invalide : {error}")
    # ... update query

@router.post("/{skill_id}/toggle", response_model=SkillResponse)
async def toggle_skill(
    skill_id: str,
    admin=Depends(require_admin),
    db=Depends(get_db),
):
    """Active/désactive un skill."""

@router.post("/{skill_id}/test", response_model=SkillTestResponse)
async def test_skill(
    skill_id: str,
    body: SkillTestRequest,
    admin=Depends(require_admin),
    db=Depends(get_db),
    registry=Depends(get_skill_registry),
):
    """
    Teste un skill avec des paramètres fictifs.
    Retourne le résultat ou l'erreur.
    """
    skill = await db.fetch_one("SELECT * FROM skills WHERE id = $1", skill_id)
    context = {"db": db, "rag": get_rag_engine(), "entreprise_id": None}

    try:
        result = await registry.execute_skill(skill["nom"], body.params, context)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.delete("/{skill_id}")
async def delete_skill(
    skill_id: str,
    admin=Depends(require_admin),
    db=Depends(get_db),
):
    """Supprime un skill. Les builtins ne peuvent pas être supprimés."""
    skill = await db.fetch_one("SELECT * FROM skills WHERE id = $1", skill_id)
    if skill["handler_key"].startswith("builtin."):
        raise HTTPException(400, "Impossible de supprimer un skill builtin. Désactivez-le.")
    await db.execute("DELETE FROM skills WHERE id = $1", skill_id)
```

### Admin - Référentiels ESG

```python
# === backend/app/api/admin/referentiels.py ===

router = APIRouter(prefix="/api/admin/referentiels", tags=["admin-referentiels"])

# --- Schemas ---
class ReferentielCreateRequest(BaseModel):
    nom: str
    code: str                    # "bceao_fd_2024" (unique)
    institution: str | None = None
    description: str | None = None
    region: str | None = None    # "UEMOA", "International", "Europe"
    grille_json: dict            # Grille complète : piliers, critères, poids

class ReferentielUpdateRequest(BaseModel):
    nom: str | None = None
    description: str | None = None
    grille_json: dict | None = None
    is_active: bool | None = None

class ReferentielPreviewRequest(BaseModel):
    data: dict                   # Données test pour simuler un scoring

# --- Endpoints ---
@router.get("/", response_model=list[ReferentielResponse])
async def list_referentiels(
    region: str | None = None,
    admin=Depends(require_admin),
    db=Depends(get_db),
):
    """Liste tous les référentiels ESG (actifs et inactifs)."""

@router.post("/", response_model=ReferentielResponse)
async def create_referentiel(
    body: ReferentielCreateRequest,
    admin=Depends(require_admin),
    db=Depends(get_db),
):
    """
    Crée un nouveau référentiel ESG.
    Valide la structure de grille_json (piliers, critères, poids).
    """
    valid, error = validate_grille(body.grille_json)
    if not valid:
        raise HTTPException(400, f"Grille invalide : {error}")
    # ... insert

@router.get("/{referentiel_id}", response_model=ReferentielDetailResponse)
async def get_referentiel(
    referentiel_id: str,
    admin=Depends(require_admin),
    db=Depends(get_db),
):
    """Détail d'un référentiel avec sa grille complète et les fonds liés."""

@router.put("/{referentiel_id}", response_model=ReferentielResponse)
async def update_referentiel(
    referentiel_id: str,
    body: ReferentielUpdateRequest,
    admin=Depends(require_admin),
    db=Depends(get_db),
):
    """Modifie un référentiel. Valide la grille si modifiée."""

@router.post("/{referentiel_id}/toggle")
async def toggle_referentiel(
    referentiel_id: str,
    admin=Depends(require_admin),
    db=Depends(get_db),
):
    """Active/désactive un référentiel."""

@router.post("/{referentiel_id}/preview", response_model=ScorePreviewResponse)
async def preview_scoring(
    referentiel_id: str,
    body: ReferentielPreviewRequest,
    admin=Depends(require_admin),
    db=Depends(get_db),
):
    """
    Simule un scoring avec des données test.
    Ne sauvegarde rien en BDD — juste un aperçu.
    Utile pour l'admin quand il ajuste les poids.
    """

def validate_grille(grille: dict) -> tuple[bool, str]:
    """Vérifie que la grille est bien structurée."""
    if "piliers" not in grille:
        return False, "La clé 'piliers' est requise"
    for pilier_key, pilier in grille["piliers"].items():
        if "poids_global" not in pilier:
            return False, f"pilier '{pilier_key}': 'poids_global' manquant"
        if "criteres" not in pilier or not pilier["criteres"]:
            return False, f"pilier '{pilier_key}': 'criteres' manquant ou vide"
        total_poids = sum(c.get("poids", 0) for c in pilier["criteres"])
        if abs(total_poids - 1.0) > 0.01:
            return False, f"pilier '{pilier_key}': somme des poids = {total_poids}, doit être 1.0"
    total_global = sum(p["poids_global"] for p in grille["piliers"].values())
    if abs(total_global - 1.0) > 0.01:
        return False, f"Somme des poids globaux = {total_global}, doit être 1.0"
    return True, "OK"
```

## Endpoint Audio (STT)

```python
# === backend/app/api/chat.py ===

@router.post("/conversations/{conversation_id}/audio")
async def send_audio_message(
    conversation_id: str,
    audio: UploadFile,
    user=Depends(get_current_user),
    db=Depends(get_db),
    agent=Depends(get_agent_engine),
    stt=Depends(get_stt_service),
):
    """
    Reçoit un fichier audio, le transcrit via STT,
    puis injecte le texte dans la boucle agent comme un message classique.

    Formats acceptés : webm, wav, mp3, ogg (sortie MediaRecorder)
    Retourne un SSE stream identique à /message.
    """
    # 1. Transcrire l'audio en texte
    transcript = await stt.transcribe(audio.file, language="fr")

    # 2. Même logique que send_message, avec transcript comme message
    async def event_generator():
        # Envoyer d'abord la transcription au frontend
        yield {"event": "transcript", "data": json.dumps({"text": transcript})}
        # Puis lancer l'agent normalement
        async for event in agent.run(
            conversation_id=conversation_id,
            user_message=transcript,
            entreprise=await get_entreprise_for_conversation(conversation_id, db),
        ):
            yield {"event": event["type"], "data": json.dumps(event)}

    return EventSourceResponse(event_generator())
```

---

## Middleware et Dépendances

```python
# === backend/app/core/dependencies.py ===

# JWT Auth
async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    user = await db.fetch_one("SELECT * FROM users WHERE id = $1", payload["sub"])
    if not user or not user["is_active"]:
        raise HTTPException(401, "Utilisateur non autorisé")
    return user

# Admin check
async def require_admin(user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(403, "Accès réservé aux administrateurs")
    return user
```

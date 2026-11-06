import gradio as gr
import requests
import time
import html

BACKEND_URL = "http://backend:5000/summarize"
HEALTH_URL = "http://backend:5000/health"

def check_backend():
    """Vérifie si le backend est disponible"""
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        return response.status_code == 200
    except:
        return False

def summarize_text(text, max_length, min_length):
    """Envoie le texte au backend pour résumé"""
    
    if not text or len(text.strip()) == 0:
        return """
<div class="error-message">
<h3>Texte manquant</h3>
<p>Veuillez entrer un texte à résumer dans le champ de saisie.</p>
</div>
"""
    
    # Vérifier le nombre de mots
    word_count = len(text.split())
    if word_count < 30:
        return f"""
<div class="error-message">
<h3>Texte trop court</h3>
<p>Vous avez saisi <strong>{word_count} mots</strong>. Le minimum requis est de <strong>30 mots</strong>.</p>
<p>Veuillez ajouter plus de contenu pour générer un résumé.</p>
</div>
"""
    
    if not check_backend():
        return """
<div class="error-message">
<h3>Service indisponible</h3>
<p>Le service de résumé n'est pas disponible pour le moment. Veuillez réessayer dans quelques instants.</p>
</div>
"""
    
    try:
        response = requests.post(
            BACKEND_URL,
            json={
                'text': text,
                'max_length': max_length,
                'min_length': min_length
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            compression_rate = (1 - result['summary_length']/result['original_length'])*100
            safe_summary = html.escape(str(result['summary']))
            
            summary_text = f"""
<div class="summary-container">
<div class="stats-box">
<h3>Statistiques du résumé</h3>
<div class="stats-grid">
<div class="stat-item">
<div class="stat-label">Longueur originale</div>
<div class="stat-value">{result['original_length']}</div>
<div class="stat-unit">mots</div>
</div>
<div class="stat-item">
<div class="stat-label">Longueur du résumé</div>
<div class="stat-value">{result['summary_length']}</div>
<div class="stat-unit">mots</div>
</div>
<div class="stat-item">
<div class="stat-label">Taux de compression</div>
<div class="stat-value">{compression_rate:.1f}%</div>
<div class="stat-unit">réduction</div>
</div>
</div>
</div>

<div class="summary-box">
<h3>Résumé généré</h3>
<div class="summary-content">
{safe_summary}
</div>
</div>
</div>
"""
            return summary_text
        else:
            error = html.escape(str(response.json().get('error', 'Erreur inconnue')))
            return f"""
<div class="error-message">
<h3>Erreur de traitement</h3>
<p>{error}</p>
</div>
"""
            
    except requests.exceptions.Timeout:
        return """
<div class="error-message">
<h3>Délai d'attente dépassé</h3>
<p>Le serveur met trop de temps à répondre. Veuillez réessayer avec un texte plus court ou vérifier votre connexion.</p>
</div>
"""
    except Exception as e:
        return f"""
<div class="error-message">
<h3>Erreur technique</h3>
<p>{html.escape(str(e))}</p>
</div>
"""

# CSS personnalisé pour une interface moderne et professionnelle
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

.gradio-container,
.gradio-container * {
    box-sizing: border-box;
}

.gradio-container {
    font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
    background: #F5F7FB;
    min-height: 100vh;
}

.main-header {
    background: linear-gradient(135deg, #4F6BED 0%, #7652A8 100%);
    padding: 40px 30px;
    border-radius: 16px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
    margin-bottom: 30px;
    text-align: center;
    color: white;
}

.main-title {
    font-size: 2.8em;
    font-weight: 700;
    margin: 0 0 15px 0;
    letter-spacing: -0.5px;
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.subtitle {
    font-size: 1.2em;
    font-weight: 300;
    margin: 0;
    opacity: 0.95;
    letter-spacing: 0.3px;
}

.instructions-box {
    background: white;
    padding: 30px;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    margin-bottom: 30px;
    border-left: 4px solid #667eea;
}

.instructions-box h2 {
    color: #2d3748;
    font-size: 1.5em;
    font-weight: 600;
    margin: 0 0 20px 0;
    display: flex;
    align-items: center;
    gap: 10px;
}

.instructions-box ol {
    margin: 0;
    padding-left: 25px;
    color: #4a5568;
    line-height: 1.8;
}

.instructions-box li {
    margin-bottom: 12px;
    font-size: 1.05em;
}

.instructions-box strong {
    color: #667eea;
    font-weight: 600;
}

.section-title {
    font-size: 1.4em;
    font-weight: 600;
    color: #2d3748;
    margin: 0 0 15px 0;
    padding-bottom: 10px;
    border-bottom: 2px solid #e2e8f0;
}

.input-section {
    background: white;
    padding: 25px;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    margin-bottom: 20px;
}

.word-counter {
    background: #f7fafc;
    padding: 12px 18px;
    border-radius: 8px;
    margin: 15px 0;
    border-left: 3px solid #667eea;
    font-weight: 500;
    color: #2d3748;
}

.word-counter.warning {
    border-left-color: #f59e0b;
    background: #fffbeb;
    color: #92400e;
}

.word-counter.success {
    border-left-color: #10b981;
    background: #ecfdf5;
    color: #065f46;
}

.params-section {
    background: white;
    padding: 25px;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    margin-bottom: 20px;
}

.button-group {
    display: flex;
    gap: 15px;
    margin-top: 20px;
}

.output-section {
    background: white;
    padding: 25px;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    min-height: 400px;
}

.summary-container {
    animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.stats-box {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 25px;
    border-radius: 12px;
    margin-bottom: 25px;
    color: white;
}

.stats-box h3 {
    margin: 0 0 20px 0;
    font-size: 1.3em;
    font-weight: 600;
    color: white;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
}

.stat-item {
    background: rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(10px);
    padding: 20px;
    border-radius: 10px;
    text-align: center;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.stat-label {
    font-size: 0.9em;
    opacity: 0.9;
    margin-bottom: 8px;
    font-weight: 500;
}

.stat-value {
    font-size: 2em;
    font-weight: 700;
    margin: 5px 0;
}

.stat-unit {
    font-size: 0.85em;
    opacity: 0.8;
    margin-top: 5px;
}

.summary-box {
    background: #f7fafc;
    padding: 25px;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
}

.summary-box h3 {
    margin: 0 0 20px 0;
    font-size: 1.3em;
    font-weight: 600;
    color: #2d3748;
    padding-bottom: 15px;
    border-bottom: 2px solid #e2e8f0;
}

.summary-content {
    font-size: 1.1em;
    line-height: 1.8;
    color: #4a5568;
    background: white;
    padding: 20px;
    border-radius: 8px;
    border-left: 4px solid #667eea;
}

.error-message {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-left: 4px solid #ef4444;
    padding: 25px;
    border-radius: 12px;
    color: #991b1b;
}

.error-message h3 {
    margin: 0 0 10px 0;
    color: #dc2626;
    font-size: 1.3em;
    font-weight: 600;
}

.error-message p {
    margin: 8px 0;
    line-height: 1.6;
}

.welcome-box {
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    padding: 30px;
    border-radius: 12px;
    border: 1px solid #bae6fd;
}

.welcome-box h3 {
    color: #0369a1;
    font-size: 1.4em;
    font-weight: 600;
    margin: 0 0 20px 0;
}

.info-section {
    margin-top: 25px;
}

.info-section h4 {
    color: #0369a1;
    font-size: 1.1em;
    font-weight: 600;
    margin: 20px 0 10px 0;
}

.info-section ul {
    margin: 0;
    padding-left: 25px;
    color: #0c4a6e;
    line-height: 1.8;
}

.info-section li {
    margin-bottom: 8px;
}

.gradio-container button {
    transition: all 0.3s ease;
    border-radius: 8px !important;
    font-weight: 500 !important;
}

.gradio-container button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.gradio-container input[type="text"],
.gradio-container textarea {
    border-radius: 8px !important;
    border: 2px solid #e2e8f0 !important;
    transition: all 0.3s ease !important;
}

.gradio-container input[type="text"]:focus,
.gradio-container textarea:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
}

/* Accessible light dashboard overrides, scoped to this Gradio application. */
.gradio-container {
    color-scheme: light;
    color: #172033;
    --body-background-fill: #F5F7FB;
    --background-fill-primary: #FFFFFF;
    --background-fill-secondary: #F5F7FB;
    --body-text-color: #172033;
    --body-text-color-subdued: #475569;
    --border-color-primary: #DCE3EF;
    --input-background-fill: #FFFFFF;
    --input-border-color: #DCE3EF;
    --input-placeholder-color: #64748B;
    --button-primary-background-fill: #4F6BED;
    --button-primary-background-fill-hover: #3F59D6;
    --button-primary-text-color: #FFFFFF;
    --button-secondary-background-fill: #FFFFFF;
    --button-secondary-background-fill-hover: #EEF2FF;
    --button-secondary-text-color: #172033;
    background: #F5F7FB !important;
    width: min(100%, 1400px);
    max-width: 1400px;
    overflow-x: hidden;
}

.gradio-container .block,
.gradio-container .form,
.gradio-container .wrap {
    min-width: 0;
}

.gradio-container .dashboard-card {
    background: #FFFFFF !important;
    border: 1px solid #DCE3EF !important;
    border-radius: 14px !important;
    padding: 22px !important;
    box-shadow: 0 8px 24px rgba(23, 32, 51, 0.06) !important;
}

.gradio-container .dashboard-card > .block,
.gradio-container .dashboard-card > .form,
.gradio-container .dashboard-card .source-input,
.gradio-container .dashboard-card .parameter-slider {
    background: #FFFFFF !important;
}

.gradio-container .dashboard-row {
    align-items: stretch;
    gap: 16px;
}

.gradio-container .main-header {
    border: 1px solid rgba(255, 255, 255, 0.18);
    box-shadow: 0 14px 36px rgba(79, 107, 237, 0.20);
}

.gradio-container .main-title,
.gradio-container .subtitle {
    color: #FFFFFF !important;
    overflow-wrap: anywhere;
}

.gradio-container .subtitle {
    font-weight: 400;
    opacity: 1;
}

.gradio-container .instructions-box {
    color: #172033 !important;
    background: #FFFFFF;
    border: 1px solid #DCE3EF;
    border-left: 5px solid #4F6BED;
    border-radius: 14px;
    box-shadow: 0 8px 24px rgba(23, 32, 51, 0.06);
}

.gradio-container .instructions-box h2,
.gradio-container .instructions-box ol,
.gradio-container .instructions-box li,
.gradio-container .instructions-box p {
    color: #172033 !important;
    overflow-wrap: anywhere;
}

.gradio-container .instructions-box li::marker {
    color: #4F6BED;
    font-weight: 700;
}

.gradio-container .instructions-note {
    margin: 20px 0 0;
    padding: 16px 18px;
    color: #25324A !important;
    background: #EEF2FF;
    border: 1px solid #C7D2FE;
    border-radius: 10px;
}

.gradio-container .instructions-note strong {
    color: #3349A8 !important;
}

.gradio-container .section-title {
    color: #172033 !important;
    background: #FFFFFF !important;
    border-bottom-color: #DCE3EF;
}

.gradio-container .source-input textarea {
    min-height: 390px;
    color: #172033 !important;
    background: #FFFFFF !important;
    border: 1px solid #B8C4D8 !important;
    line-height: 1.65;
}

.gradio-container .source-input textarea::placeholder {
    color: #64748B !important;
    opacity: 1;
}

.gradio-container .source-input textarea:focus {
    border-color: #4F6BED !important;
    box-shadow: 0 0 0 3px rgba(79, 107, 237, 0.18) !important;
}

.gradio-container .parameter-slider label,
.gradio-container .parameter-slider .label-wrap,
.gradio-container .parameter-slider input {
    color: #172033 !important;
}

.gradio-container .parameter-slider .info {
    color: #475569 !important;
}

.gradio-container .primary-action,
.gradio-container .secondary-action {
    min-height: 48px;
    border-radius: 10px !important;
    font-weight: 650 !important;
}

.gradio-container .primary-action {
    color: #FFFFFF !important;
    background: #4F6BED !important;
    border-color: #4F6BED !important;
}

.gradio-container .primary-action:hover {
    background: #3F59D6 !important;
}

.gradio-container .secondary-action {
    color: #172033 !important;
    background: #FFFFFF !important;
    border: 1px solid #B8C4D8 !important;
}

.gradio-container button:focus-visible,
.gradio-container textarea:focus-visible,
.gradio-container input:focus-visible {
    outline: 3px solid rgba(79, 107, 237, 0.32) !important;
    outline-offset: 2px;
}

.gradio-container button:disabled {
    cursor: not-allowed;
    opacity: 0.58;
    transform: none !important;
    box-shadow: none !important;
}

.gradio-container .result-panel,
.gradio-container .result-panel > div {
    color: #172033;
}

.gradio-container .welcome-box {
    color: #172033;
    background: #F8FAFF;
    border-color: #DCE3EF;
}

.gradio-container .welcome-box h3,
.gradio-container .info-section h4 {
    color: #3349A8 !important;
}

.gradio-container .welcome-box p,
.gradio-container .info-section ul,
.gradio-container .info-section li {
    color: #475569 !important;
}

.gradio-container .stats-box {
    background: linear-gradient(135deg, #4F6BED 0%, #7652A8 100%);
}

.gradio-container .stat-label,
.gradio-container .stat-value,
.gradio-container .stat-unit,
.gradio-container .stats-box h3 {
    color: #FFFFFF !important;
    opacity: 1;
}

.gradio-container .summary-box {
    background: #F8FAFC;
    border-color: #DCE3EF;
}

.gradio-container .summary-box h3 {
    color: #172033 !important;
    border-bottom-color: #DCE3EF;
}

.gradio-container .summary-content {
    color: #172033 !important;
    background: #FFFFFF;
    border: 1px solid #DCE3EF;
    border-left: 4px solid #4F6BED;
}

.gradio-container .error-message,
.gradio-container .error-message p {
    color: #7F1D1D !important;
}

.gradio-container .error-message h3 {
    color: #B91C1C !important;
}

@media (max-width: 768px) {
    html,
    body {
        width: 100%;
        max-width: 100%;
        overflow-x: hidden;
    }

    .stats-grid {
        grid-template-columns: 1fr;
    }
    
    .main-title {
        font-size: 2em;
    }
    
    .gradio-container {
        width: 100%;
        min-width: 0 !important;
        max-width: 100% !important;
        padding: 10px;
        margin: 0;
    }

    .gradio-container .main,
    .gradio-container .contain,
    .gradio-container .wrap,
    .gradio-container .block,
    .gradio-container .main-header,
    .gradio-container .instructions-box {
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
    }

    .gradio-container .main-title,
    .gradio-container .subtitle,
    .gradio-container .instructions-box li,
    .gradio-container .instructions-note {
        white-space: normal !important;
        overflow-wrap: anywhere;
        word-break: normal;
    }

    .gradio-container .dashboard-row {
        flex-direction: column;
        flex-wrap: nowrap;
    }

    .gradio-container .dashboard-row > div {
        width: 100% !important;
        min-width: 0 !important;
        flex: 1 1 auto !important;
    }

    .gradio-container .dashboard-card,
    .gradio-container .instructions-box {
        padding: 18px !important;
    }

    .gradio-container .source-input textarea {
        min-height: 280px;
    }

    .gradio-container .main-header {
        padding: 28px 18px;
    }
}
"""

with gr.Blocks(title="Système de Résumé Automatique", theme=gr.themes.Base(), css=custom_css) as interface:
    
    gr.HTML(
        """
        <div class="main-header">
            <div class="main-title">Système de Résumé Automatique par Intelligence Artificielle</div>
            <div class="subtitle">Résumé automatique de textes utilisant le réseau de neurones BART</div>
        </div>
        """
    )
    
    gr.HTML(
        """
        <div class="instructions-box">
            <h2>Mode d'emploi</h2>
            <ol>
                <li>Saisissez ou collez votre texte dans le champ de saisie ci-dessous (minimum 30 mots)</li>
                <li>Ajustez les paramètres de longueur du résumé selon vos besoins</li>
                <li>Cliquez sur "Générer le résumé" pour traiter votre texte</li>
                <li>Le système analysera et produira un résumé concis et précis</li>
            </ol>
            <p class="instructions-note">
                <strong>Note importante :</strong> Ce modèle fonctionne de manière optimale avec des textes en anglais.
            </p>
        </div>
        """
    )
    
    with gr.Row(elem_classes=["dashboard-row"]):
        with gr.Column(scale=1):
            with gr.Group(elem_classes=["dashboard-card", "source-card"]):
                gr.HTML('<div class="section-title">Texte source</div>')
                input_text = gr.Textbox(
                    label="",
                    placeholder="Saisissez ou collez votre texte ici (minimum 30 mots requis)...",
                    lines=20,
                    max_lines=30,
                    value="",
                    show_label=False,
                    elem_classes=["source-input"]
                )
                
                word_counter = gr.HTML('<div class="word-counter"><strong>Nombre de mots : 0</strong></div>')
            
            with gr.Group(elem_classes=["dashboard-card", "parameters-card"]):
                gr.HTML('<div class="section-title">Paramètres de résumé</div>')
                with gr.Row():
                    max_length_slider = gr.Slider(
                        minimum=50,
                        maximum=500,
                        value=150,
                        step=10,
                        label="Longueur maximale",
                        info="Nombre maximum de mots dans le résumé",
                        elem_classes=["parameter-slider"]
                    )
                    
                    min_length_slider = gr.Slider(
                        minimum=10,
                        maximum=200,
                        value=40,
                        step=5,
                        label="Longueur minimale",
                        info="Nombre minimum de mots dans le résumé",
                        elem_classes=["parameter-slider"]
                    )
            
            with gr.Row():
                submit_btn = gr.Button("Générer le résumé", variant="primary", size="lg", scale=3, elem_classes=["primary-action"])
                clear_btn = gr.Button("Effacer", variant="secondary", size="lg", scale=1, elem_classes=["secondary-action"])
        
        with gr.Column(scale=1, elem_classes=["dashboard-card", "result-card"]):
            gr.HTML('<div class="section-title">Résultat</div>')
            
            output_text = gr.HTML(
                """
                <div class="welcome-box">
                    <h3>Bienvenue dans le système de résumé automatique</h3>
                    <p>Votre résumé apparaîtra ici après le traitement de votre texte.</p>
                    
                    <div class="info-section">
                        <h4>Informations sur le système</h4>
                        <ul>
                            <li><strong>Modèle :</strong> BART (Bidirectional and Auto-Regressive Transformers)</li>
                            <li><strong>Développeur :</strong> Facebook AI Research</li>
                            <li><strong>Corpus d'entraînement :</strong> CNN/DailyMail</li>
                            <li><strong>Langue principale :</strong> Anglais</li>
                        </ul>
                        
                        <h4>Bonnes pratiques</h4>
                        <ul>
                            <li>Utilisez des textes bien structurés pour des résultats optimaux</li>
                            <li>Assurez-vous que le texte contient au moins 30 mots</li>
                            <li>Les textes en anglais donnent les meilleurs résultats</li>
                            <li>Ajustez les paramètres selon la longueur de résumé souhaitée</li>
                        </ul>
                    </div>
                </div>
                """,
                elem_classes=["result-panel"]
            )
        
    # Fonction pour compter les mots en temps réel
    def update_word_count(text):
        if text:
            count = len(text.split())
            if count < 30:
                return f'<div class="word-counter warning"><strong>Nombre de mots : {count}</strong><br><small>Minimum requis : 30 mots</small></div>'
            else:
                return f'<div class="word-counter success"><strong>Nombre de mots : {count}</strong><br><small>Texte prêt pour le résumé</small></div>'
        return '<div class="word-counter"><strong>Nombre de mots : 0</strong></div>'
    
    # Fonction pour effacer
    def clear_all():
        return "", '<div class="word-counter"><strong>Nombre de mots : 0</strong></div>', """
                <div class="welcome-box">
                    <h3>Bienvenue dans le système de résumé automatique</h3>
                    <p>Votre résumé apparaîtra ici après le traitement de votre texte.</p>
                    
                    <div class="info-section">
                        <h4>Informations sur le système</h4>
                        <ul>
                            <li><strong>Modèle :</strong> BART (Bidirectional and Auto-Regressive Transformers)</li>
                            <li><strong>Développeur :</strong> Facebook AI Research</li>
                            <li><strong>Corpus d'entraînement :</strong> CNN/DailyMail</li>
                            <li><strong>Langue principale :</strong> Anglais</li>
                        </ul>
                        
                        <h4>Bonnes pratiques</h4>
                        <ul>
                            <li>Utilisez des textes bien structurés pour des résultats optimaux</li>
                            <li>Assurez-vous que le texte contient au moins 30 mots</li>
                            <li>Les textes en anglais donnent les meilleurs résultats</li>
                            <li>Ajustez les paramètres selon la longueur de résumé souhaitée</li>
                        </ul>
                    </div>
                </div>
                """
    
    # Événements
    input_text.change(
        fn=update_word_count,
        inputs=input_text,
        outputs=word_counter
    )
    
    submit_btn.click(
        fn=summarize_text,
        inputs=[input_text, max_length_slider, min_length_slider],
        outputs=output_text
    )
    
    clear_btn.click(
        fn=clear_all,
        inputs=None,
        outputs=[input_text, word_counter, output_text]
    )

if __name__ == "__main__":
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )

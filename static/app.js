document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const questionInput = document.getElementById('question-input');
    const sendButton = document.getElementById('send-button');
    const chatHistory = document.getElementById('chat-history');
    const loadingIndicator = document.getElementById('loading-indicator');

    // In-memory array for chat history, reset on refresh as requested
    const history = [];

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const question = questionInput.value.trim();
        if (!question) return;

        // Clear input and disable form
        questionInput.value = '';
        questionInput.disabled = true;
        sendButton.disabled = true;
        
        // Add question to UI
        addQuestionToUI(question);
        
        // Show loading
        loadingIndicator.classList.remove('hidden');
        
        try {
            const response = await fetch('/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question: question,
                    top_k: 5,
                    filters: {}
                })
            });

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            const data = await response.json();
            
            // Add answer to UI and history
            addAnswerToUI(data);
            history.push({ question, answer: data });

        } catch (error) {
            console.error('Error fetching answer:', error);
            addErrorToUI(error.message);
        } finally {
            // Re-enable form and hide loading
            loadingIndicator.classList.add('hidden');
            questionInput.disabled = false;
            sendButton.disabled = false;
            questionInput.focus();
            scrollToBottom();
        }
    });

    function addQuestionToUI(question) {
        const pairDiv = document.createElement('div');
        pairDiv.className = 'chat-pair';
        
        const qBubble = document.createElement('div');
        qBubble.className = 'question-bubble';
        qBubble.textContent = question;
        
        pairDiv.appendChild(qBubble);
        chatHistory.appendChild(pairDiv);
        scrollToBottom();
        
        // Return the pairDiv so we can append the answer to it later
        return pairDiv;
    }

    function addAnswerToUI(data) {
        const pairs = document.querySelectorAll('.chat-pair');
        const currentPair = pairs[pairs.length - 1]; // Get the last pair
        
        const answerCard = document.createElement('div');
        answerCard.className = 'answer-card';

        // 1. Answer text
        const textDiv = document.createElement('div');
        textDiv.className = 'answer-text';
        
        if (data.context_found === false) {
            textDiv.classList.add('no-context');
            textDiv.textContent = "No relevant information found in the knowledge base.";
        } else {
            textDiv.textContent = data.answer;
        }
        answerCard.appendChild(textDiv);

        // 2. Sources (if any)
        if (data.context_found !== false && data.sources && data.sources.length > 0) {
            const sourcesContainer = document.createElement('div');
            sourcesContainer.className = 'sources-container';
            
            const sourcesTitle = document.createElement('h4');
            sourcesTitle.textContent = 'Sources';
            sourcesContainer.appendChild(sourcesTitle);
            
            const sourcesList = document.createElement('ul');
            sourcesList.className = 'sources-list';
            
            // Deduplicate sources by file+chunk for cleaner display
            const uniqueSources = new Map();
            data.sources.forEach(src => {
                const key = `${src.source_file}#${src.chunk_index}`;
                if (!uniqueSources.has(key)) {
                    uniqueSources.set(key, src);
                }
            });

            uniqueSources.forEach(src => {
                const li = document.createElement('li');
                li.className = 'source-item';
                
                const badge = document.createElement('span');
                badge.className = 'source-badge';
                badge.textContent = `Chunk ${src.chunk_index}`;
                
                const filename = document.createElement('span');
                filename.textContent = src.source_file;
                
                li.appendChild(badge);
                li.appendChild(filename);
                sourcesList.appendChild(li);
            });
            
            sourcesContainer.appendChild(sourcesList);
            answerCard.appendChild(sourcesContainer);
        }

        // 3. Stats row
        const statsRow = document.createElement('div');
        statsRow.className = 'stats-row';
        
        const stats = [
            { label: 'Chunks', value: data.chunks_retrieved || 0 },
            { label: 'Retrieval', value: `${(data.retrieval_latency_ms || 0).toFixed(0)}ms` },
            { label: 'Generation', value: `${(data.generation_latency_ms || 0).toFixed(0)}ms` },
            { label: 'Total', value: `${(data.total_latency_ms || 0).toFixed(0)}ms` },
        ];
        
        if (data.token_usage) {
            stats.push({ label: 'Tokens', value: data.token_usage.total_tokens || 0 });
        }

        stats.forEach(stat => {
            const statDiv = document.createElement('div');
            statDiv.className = 'stat-item';
            statDiv.innerHTML = `<span>${stat.label}:</span> <strong>${stat.value}</strong>`;
            statsRow.appendChild(statDiv);
        });
        
        answerCard.appendChild(statsRow);
        currentPair.appendChild(answerCard);
        scrollToBottom();
    }

    function addErrorToUI(message) {
        const pairs = document.querySelectorAll('.chat-pair');
        const currentPair = pairs[pairs.length - 1];
        
        const answerCard = document.createElement('div');
        answerCard.className = 'answer-card';
        
        const textDiv = document.createElement('div');
        textDiv.className = 'answer-text no-context';
        textDiv.textContent = `Error: ${message}`;
        
        answerCard.appendChild(textDiv);
        currentPair.appendChild(answerCard);
        scrollToBottom();
    }

    function scrollToBottom() {
        chatHistory.scrollTo({
            top: chatHistory.scrollHeight,
            behavior: 'smooth'
        });
    }
});

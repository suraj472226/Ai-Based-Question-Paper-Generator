document.getElementById('question-form').addEventListener('submit', function(e) {
    e.preventDefault();

    const subject = document.getElementById('subject').value;
    const difficulty = document.getElementById('difficulty').value;
    const num_questions = document.getElementById('num_questions').value;

    fetch('http://127.0.0.1:5000/generate', {  // Use localhost address
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            subject: subject,
            difficulty: difficulty,
            num_questions: num_questions
        }),
    })
    .then(response => response.json())
    .then(data => {
        let questionHTML = '<h2>Generated Questions</h2><ul>';
        data.questions.forEach(question => {
            questionHTML += `<li>${question}</li>`;
        });
        questionHTML += '</ul>';
        document.getElementById('question-paper').innerHTML = questionHTML;
    })
    .catch(error => {
        console.error('Error:', error);
    });
});

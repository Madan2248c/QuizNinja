document.addEventListener('DOMContentLoaded', function() {
    // Form validation
    const quizForm = document.getElementById('quiz-generation-form');
    if (quizForm) {
        quizForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const topic = document.getElementById('topic').value;
            const numQuestions = document.getElementById('num-questions').value;

            if (!topic || !numQuestions) {
                alert('Please fill in all fields');
                return;
            }

            // Show loading state
            quizForm.classList.add('form-loading');
            document.getElementById('submit-btn').disabled = true;

            // Submit form
            this.submit();
        });
    }

    // Quiz answer submission
    const quizAnswerForm = document.getElementById('quiz-answer-form');
    if (quizAnswerForm) {
        const submitButton = quizAnswerForm.querySelector('button[type="submit"]');

        // Enable submit button when an option is selected
        quizAnswerForm.addEventListener('change', function() {
            submitButton.disabled = false;
        });

        quizAnswerForm.addEventListener('submit', function(e) {
            const selectedOption = document.querySelector('input[name="answer"]:checked');
            if (!selectedOption) {
                e.preventDefault();
                alert('Please select an answer');
                return;
            }
            // Disable submit button to prevent double submission
            submitButton.disabled = true;
        });
    }

    // Enable tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
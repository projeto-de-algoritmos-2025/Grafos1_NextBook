function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrfToken = getCookie('csrftoken');

function toggleFavorito(livroId, heart) {
    const isFavoritado = heart.classList.contains('favorited');
    fetch(`/favoritar/${livroId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ favoritado: !isFavoritado })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            heart.classList.toggle('favorited', !isFavoritado);
            const icon = heart.querySelector('i');
            icon.classList.toggle('fas', !isFavoritado);
            icon.classList.toggle('far', isFavoritado);
        } else {
            alert('Erro ao favoritar o livro.');
        }
    })
    .catch(error => console.error('Erro:', error));
}

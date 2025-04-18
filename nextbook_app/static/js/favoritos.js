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
    const favoritar = !isFavoritado;

    fetch(`/favoritar/${livroId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({ favoritado: favoritar })
    })
    .then(response => {
        if (!response.ok) throw new Error('Erro na requisição');
        return response.json();
    })
    .then(data => {
        if (data.success) {
            heart.classList.toggle('favorited', favoritar);
            const icon = heart.querySelector('i');
            icon.classList.toggle('fas', favoritar);
            icon.classList.toggle('far', !favoritar);
        } else {
            console.error(data.error || 'Erro desconhecido');
        }
    })
    .catch(error => console.error('Erro ao favoritar:', error));
}

function toggleFavorito(livroId, heart) {
    // Obtenção do estado atual do coração (favoritado ou não)
    const isFavoritado = heart.classList.contains('favorited');
    
    // Definindo o valor para enviar na requisição POST
    const favoritar = !isFavoritado;

    // Enviando requisição para o Django via fetch
    fetch(`/favoritar/${livroId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken // O token CSRF (coloque o valor do CSRF aqui)
        },
        body: new URLSearchParams({
            'favoritar': favoritar.toString()
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Alterna a classe do ícone do coração para "favoritado" ou "não favoritado"
            heart.classList.toggle('favorited', data.favoritado);
            const icon = heart.querySelector('i');
            icon.classList.toggle('fas', data.favoritado);  // ícone preenchido
            icon.classList.toggle('far', !data.favoritado);  // ícone vazio
        } else {
            console.log(data.message); // Caso haja algum erro, exibe a mensagem
        }
    })
    .catch(error => console.error('Erro ao favoritar:', error));
}

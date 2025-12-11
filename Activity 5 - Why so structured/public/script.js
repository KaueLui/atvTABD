let currentAuthorPage = 1;
const authorLimit = 10;

let currentBookPage = 1;
const bookLimit = 10;

async function loadAuthors(page = currentAuthorPage) {
  const res = await fetch(`/authors?page=${page}&limit=${authorLimit}`);
  const authors = await res.json();

  const list = document.getElementById("authors-list");
  list.innerHTML = "";

  if (authors.length === 0 && currentAuthorPage > 1) {
    currentAuthorPage--;
    return loadAuthors(currentAuthorPage);
  }

  authors.forEach(a => {
    const div = document.createElement("div");
    div.className = "card";
    div.innerHTML = `<strong>${a.name}</strong> - ${a.nationality}`;
    list.appendChild(div);
  });

  const select = document.getElementById("book-author");
  select.innerHTML = "";
  authors.forEach(a => {
    const option = document.createElement("option");
    option.value = a._id;
    option.textContent = a.name;
    select.appendChild(option);
  });

  document.getElementById("author-page-info").textContent = `Página ${currentAuthorPage}`;
  document.getElementById("author-prev").disabled = currentAuthorPage === 1;
  document.getElementById("author-next").disabled = authors.length < authorLimit;
}

function nextAuthorPage() {
  currentAuthorPage++;
  loadAuthors();
}

function prevAuthorPage() {
  if (currentAuthorPage > 1) {
    currentAuthorPage--;
    loadAuthors();
  }
}

async function loadBooks(page = currentBookPage) {
  const res = await fetch(`/books?page=${page}&limit=${bookLimit}`);
  const books = await res.json();

  const list = document.getElementById("books-list");
  list.innerHTML = "";

  if (books.length === 0 && currentBookPage > 1) {
    currentBookPage--; 
    return loadBooks(currentBookPage);
  }

  books.forEach(b => {
    const div = document.createElement("div");
    div.className = "card";
    div.innerHTML = `
      <strong>${b.title}</strong> <br>
      Autor: ${b.author?.name ?? "Desconhecido"} <br>
      Ano: ${b.publishedYear} <br>
      Gênero: ${b.genre} <br>
      ISBN: ${b.isbn}
    `;
    list.appendChild(div);
  });

  document.getElementById("book-page-info").textContent = `Página ${currentBookPage}`;
  document.getElementById("book-prev").disabled = currentBookPage === 1;
  document.getElementById("book-next").disabled = books.length < bookLimit;
}

function nextBookPage() {
  currentBookPage++;
  loadBooks();
}

function prevBookPage() {
  if (currentBookPage > 1) {
    currentBookPage--;
    loadBooks();
  }
}

async function addAuthor() {
  const data = {
    name: document.getElementById("author-name").value,
    birthdate: document.getElementById("author-birthdate").value,
    nationality: document.getElementById("author-nationality").value
  };

  await fetch("/authors", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });

  loadAuthors(currentAuthorPage);
}

async function addBook() {
  const data = {
    title: document.getElementById("book-title").value,
    author: document.getElementById("book-author").value,
    publishedYear: Number(document.getElementById("book-year").value),
    genre: document.getElementById("book-genre").value,
    isbn: document.getElementById("book-isbn").value
  };

  await fetch("/books", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });

  loadBooks(currentBookPage);
}

loadAuthors();
loadBooks();

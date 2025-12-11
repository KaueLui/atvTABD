import mongoose from "mongoose";
// Representa um autor e a lista de livros associados
const AuthorSchema = new mongoose.Schema({
  name: { type: String, required: true },  
  birthdate: { type: Date, required: true },
  nationality: { type: String, required: true },
  books: [{ type: mongoose.Schema.Types.ObjectId, ref: "Book" }]
});

export default mongoose.model("Author", AuthorSchema);

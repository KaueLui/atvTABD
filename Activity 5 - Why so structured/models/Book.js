import mongoose from "mongoose";
// Cada livro pertence a um autor
const BookSchema = new mongoose.Schema({
  title: { type: String, required: true }, 
  author: { type: mongoose.Schema.Types.ObjectId, ref: "Author", required: true }, 
  publishedYear: { type: Number, required: true },  
  genre: { type: String, required: true }, 
  isbn: { type: String, unique: true, required: true }
});

export default mongoose.model("Book", BookSchema);

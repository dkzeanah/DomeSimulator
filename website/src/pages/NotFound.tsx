import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-xl px-4 py-16 text-center">
      <h1 className="text-4xl font-bold">Nothing stands here yet</h1>
      <p className="muted mt-3">That page does not exist.</p>
      <Link className="btn mt-6" to="/">Back to the build</Link>
    </div>
  );
}

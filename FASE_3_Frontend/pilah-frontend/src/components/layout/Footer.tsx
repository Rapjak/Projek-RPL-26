export function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          <div>
            <h3 className="font-bold text-gray-900 mb-4">Pilah.in</h3>
            <p className="text-sm text-gray-600">
              Platform untuk klasifikasi sampah dan edukasi lingkungan
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-4">Produk</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li><a href="#" className="hover:text-emerald-600">Upload</a></li>
              <li><a href="#" className="hover:text-emerald-600">History</a></li>
              <li><a href="#" className="hover:text-emerald-600">Rewards</a></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-4">Edukasi</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li><a href="#" className="hover:text-emerald-600">Materials</a></li>
              <li><a href="#" className="hover:text-emerald-600">Guides</a></li>
              <li><a href="#" className="hover:text-emerald-600">Tips</a></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-4">Legal</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li><a href="#" className="hover:text-emerald-600">Privacy</a></li>
              <li><a href="#" className="hover:text-emerald-600">Terms</a></li>
              <li><a href="#" className="hover:text-emerald-600">Contact</a></li>
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-200 pt-8 text-center text-sm text-gray-600">
          <p>&copy; 2026 Pilah.in. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}

import VirtualizedList from './components/VirtualizedList'

function App() {
  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Generated Component Demo</h1>
        
        <div className="space-y-8 bg-white p-8 rounded-lg shadow">
          <section>
            <h2 className="text-xl font-semibold mb-4">Component Showcase</h2>
            <VirtualizedList />
          </section>
        </div>
      </div>
    </div>
  )
}

export default App

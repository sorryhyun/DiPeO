import Button from './components/Button'

function App() {
  const handleClick = () => {
    alert('Button clicked!')
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Button Component Demo</h1>
        
        <div className="space-y-8 bg-white p-8 rounded-lg shadow">
          <section>
            <h2 className="text-xl font-semibold mb-4">Variants</h2>
            <div className="flex gap-4 flex-wrap">
              <Button variant="solid" onClick={handleClick}>Solid</Button>
              <Button variant="outline" onClick={handleClick}>Outline</Button>
              <Button variant="ghost" onClick={handleClick}>Ghost</Button>
              <Button variant="link" onClick={handleClick}>Link</Button>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-4">Sizes</h2>
            <div className="flex gap-4 items-center flex-wrap">
              <Button size="xs" onClick={handleClick}>Extra Small</Button>
              <Button size="sm" onClick={handleClick}>Small</Button>
              <Button size="md" onClick={handleClick}>Medium</Button>
              <Button size="lg" onClick={handleClick}>Large</Button>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-4">States</h2>
            <div className="flex gap-4 flex-wrap">
              <Button onClick={handleClick}>Normal</Button>
              <Button loading onClick={handleClick}>Loading</Button>
              <Button disabled onClick={handleClick}>Disabled</Button>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-4">With Icons</h2>
            <div className="flex gap-4 flex-wrap">
              <Button leftIcon={<span>⬅️</span>} onClick={handleClick}>
                Left Icon
              </Button>
              <Button rightIcon={<span>➡️</span>} onClick={handleClick}>
                Right Icon
              </Button>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-4">Polymorphic</h2>
            <div className="flex gap-4 flex-wrap">
              <Button as="a" href="#" variant="outline">
                As Anchor
              </Button>
              <Button as="div" variant="ghost" onClick={handleClick}>
                As Div
              </Button>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-4">Full Width</h2>
            <Button fullWidth onClick={handleClick}>
              Full Width Button
            </Button>
          </section>
        </div>
      </div>
    </div>
  )
}

export default App

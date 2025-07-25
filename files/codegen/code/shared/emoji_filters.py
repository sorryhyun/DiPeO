def emoji_to_icon(emoji: str) -> str:
    """Convert emoji to icon name (for lucide-react)."""
    emoji_icon_map = {
        '🤖': 'Bot',
        '📝': 'FileText',
        '💾': 'Database',
        '🔧': 'Wrench',
        '⚡': 'Zap',
        '🔄': 'RefreshCw',
        '🌐': 'Globe',
        '📊': 'BarChart',
        '📈': 'TrendingUp',
        '🔍': 'Search',
        '⚙️': 'Settings',
        '📁': 'Folder',
        '📂': 'FolderOpen',
        '🚀': 'Rocket',
        '🎯': 'Target',
        '✅': 'Check',
        '❌': 'X',
        '⏱️': 'Timer',
        '📅': 'Calendar',
        '💡': 'Lightbulb',
        '🔐': 'Lock',
        '🔓': 'Unlock',
        '📧': 'Mail',
        '💬': 'MessageSquare',
        '👤': 'User',
        '👥': 'Users',
        '🏷️': 'Tag',
        '📎': 'Paperclip',
        '🔗': 'Link',
        '⚠️': 'AlertTriangle',
        'ℹ️': 'Info',
        '❓': 'HelpCircle',
        '🎨': 'Palette',
        '📸': 'Camera',
        '🎵': 'Music',
        '🎬': 'Film',
        '📺': 'Tv',
        '📻': 'Radio',
        '🔊': 'Volume2',
        '🔇': 'VolumeX',
        '🔔': 'Bell',
        '🔕': 'BellOff',
        '📍': 'MapPin',
        '🗺️': 'Map',
        '🧭': 'Compass',
        '🏠': 'Home',
        '🏢': 'Building',
        '🏭': 'Factory',
        '🏥': 'Building2',
        '🏦': 'Landmark',
        '✈️': 'Plane',
        '🚗': 'Car',
        '🚌': 'Bus',
        '🚆': 'Train',
        '🚢': 'Ship',
        '🚁': 'Plane',
        '⏰': 'Clock',
        '⌚': 'Watch',
        '📱': 'Smartphone',
        '💻': 'Laptop',
        '🖥️': 'Monitor',
        '🖨️': 'Printer',
        '⌨️': 'Keyboard',
        '🖱️': 'Mouse',
        '💿': 'Disc',
        '💵': 'DollarSign',
        '💳': 'CreditCard',
        '📉': 'TrendingDown',
        '📊': 'BarChart2',
        '📋': 'Clipboard',
        '📌': 'Pin',
        '📏': 'Ruler',
        '✂️': 'Scissors',
        '🖊️': 'Pen',
        '✏️': 'Pencil',
        '📚': 'BookOpen',
        '📖': 'Book',
        '🔖': 'Bookmark',
        '🏷️': 'Tags',
        '🎁': 'Gift',
        '🎉': 'PartyPopper',
        '🎈': 'Sparkles',
        '🎯': 'Target',
        '🏆': 'Trophy',
        '🥇': 'Medal',
        '⚽': 'Circle',
        '🏀': 'Circle',
        '🎾': 'Circle',
        '🎮': 'Gamepad2',
        '🎲': 'Dices',
        '🧩': 'Puzzle',
        '🔥': 'Flame',
        '💧': 'Droplet',
        '🌟': 'Star',
        '⭐': 'Star',
        '🌙': 'Moon',
        '☀️': 'Sun',
        '⛅': 'CloudSun',
        '☁️': 'Cloud',
        '🌧️': 'CloudRain',
        '⛈️': 'CloudLightning',
        '❄️': 'Snowflake',
        '🌈': 'Rainbow',
        '🌊': 'Waves',
        '🍃': 'Leaf',
        '🌺': 'Flower',
        '🌻': 'Flower2',
        '🌲': 'Trees',
        '🌳': 'TreePine',
        '🌴': 'Palmtree',
        '🌵': 'Cactus',
        '🍀': 'Clover',
        '🍄': 'Mushroom',
        '🌰': 'Nut',
        '🦋': 'Bug',
        '🐛': 'Bug',
        '🐝': 'Bug',
        '🐞': 'Bug',
        '🦗': 'Bug',
        '🕷️': 'Bug',
        '🦂': 'Bug',
        '🐢': 'Turtle',
        '🐍': 'Worm',
        '🦎': 'Fish',
        '🦖': 'Fish',
        '🦕': 'Fish',
        '🐙': 'Fish',
        '🦑': 'Fish',
        '🦐': 'Fish',
        '🦞': 'Fish',
        '🦀': 'Fish',
        '🐡': 'Fish',
        '🐠': 'Fish',
        '🐟': 'Fish',
        '🐬': 'Fish',
        '🐳': 'Fish',
        '🐋': 'Fish',
        '🦈': 'Fish',
        '🐊': 'Fish',
        '🐅': 'Cat',
        '🐆': 'Cat',
        '🦓': 'GitBranch',
        '🦍': 'User',
        '🦧': 'User',
        '🦣': 'Database',
        '🐘': 'Database',
        '🦛': 'Database',
        '🦏': 'Shield',
        '🐪': 'Mountain',
        '🐫': 'Mountain',
        '🦒': 'GitCommit',
        '🦘': 'Activity',
        '🦬': 'HardDrive',
        '🐃': 'HardDrive',
        '🐂': 'HardDrive',
        '🐄': 'HardDrive',
        '🐎': 'Zap',
        '🐖': 'Package',
        '🐏': 'Cloud',
        '🐑': 'Cloud',
        '🦙': 'Layers',
        '🐐': 'Triangle',
        '🦌': 'GitBranch',
        '🐕': 'Heart',
        '🐩': 'Heart',
        '🦮': 'Eye',
        '🐕‍🦺': 'Shield',
        '🐈': 'Cat',
        '🐈‍⬛': 'Moon',
        '🐓': 'Sun',
        '🦃': 'Package',
        '🦆': 'Droplet',
        '🦢': 'Feather',
        '🦅': 'Send',
        '🦉': 'Moon',
        '🦇': 'Moon',
        '🐺': 'AlertTriangle',
        '🦊': 'Cpu',
        '🦝': 'Eye',
        '🐗': 'Package',
        '🐴': 'Zap',
        '🦄': 'Sparkles',
        '🐝': 'Hexagon',
        '🐛': 'Bug',
        '🦋': 'Wind',
        '🐌': 'Loader',
        '🐞': 'Bug',
        '🐜': 'Activity',
        '🦟': 'Radio',
        '🦗': 'Radio',
        '🕷️': 'Globe',
        '🦂': 'AlertTriangle',
        '🐢': 'Shield',
        '🐍': 'GitCommit',
        '🦎': 'Activity',
        '🦖': 'AlertTriangle',
        '🦕': 'BarChart',
        '🐙': 'GitBranch',
        '🦑': 'GitMerge',
        '🦐': 'MoreHorizontal',
        '🦞': 'Scissors',
        '🦀': 'Move',
        '🐡': 'Circle',
        '🐠': 'Fish',
        '🐟': 'Fish',
        '🐬': 'Activity',
        '🐳': 'Database',
        '🐋': 'Database',
        '🦈': 'AlertTriangle',
        '🐊': 'AlertTriangle',
        '🐅': 'Zap',
        '🐆': 'Zap',
        '🦓': 'BarChart',
        '🦍': 'Shield',
        '🦧': 'User',
        '🦣': 'Database',
        '🐘': 'Database',
        '🦛': 'Package',
        '🦏': 'Shield',
        '🐪': 'BarChart',
        '🐫': 'BarChart',
        '🦒': 'GitCommit',
        '🦘': 'Activity',
        '🦬': 'HardDrive',
        '🐃': 'HardDrive',
        '🐂': 'HardDrive',
        '🐄': 'Package',
        '🐎': 'Zap',
        '🐖': 'Package',
        '🐏': 'Cloud',
        '🐑': 'Cloud',
        '🦙': 'Layers',
        '🐐': 'Triangle',
        '🦌': 'GitBranch',
        '🐕': 'Heart',
        '🐩': 'Scissors',
        '🦮': 'Eye',
        '🐕‍🦺': 'Shield',
        '🐈': 'Hash',
        '🐈‍⬛': 'Moon',
        '🪶': 'Feather',
        '🐓': 'Sun',
        '🦃': 'Package',
        '🦆': 'Droplet',
        '🦢': 'Feather',
        '🦅': 'Send',
        '🦉': 'Moon',
        '🦇': 'Moon',
        '🐺': 'AlertTriangle',
        '🦊': 'Cpu',
        '🦝': 'Eye',
        '🐗': 'Package',
        '🐴': 'Zap',
        '🦄': 'Sparkles',
    }
    return emoji_icon_map.get(emoji, 'Circle')

clsx usage guide
- Import: import clsx from 'clsx';
- Merge conditions succinctly:
  const classes = clsx(base, isActive && 'bg-green-500', className);
- This project uses a small wrapper (cx) around clsx for consistency:
  import { cx } from '../Button/Button.styles';
  const classes = cx(base, isActive && 'bg-green-500', className);
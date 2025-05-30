import React from 'react';
import clsx from 'clsx';

interface SwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  id?: string;
}

export const Switch: React.FC<SwitchProps> = ({ checked, onChange, label, id }) => {
  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onChange(event.target.checked);
  };

  return (
    <label htmlFor={id} className="flex items-center cursor-pointer">
      <div className="relative">
        <input id={id} type="checkbox" className="sr-only" checked={checked} onChange={handleChange} />
        <div className={clsx("block w-10 h-6 rounded-full", checked ? "bg-blue-600" : "bg-gray-300")}></div>
        <div
          className={clsx(
            "dot absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform",
            checked ? "transform translate-x-full" : ""
          )}
        ></div>
      </div>
      {label && <span className="ml-2 text-sm text-gray-700">{label}</span>}
    </label>
  );
};
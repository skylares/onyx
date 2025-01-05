import { MoreHorizontal } from "lucide-react";
import { useRef, useState, useEffect } from "react";

interface DropdownMenuProps {
  children: React.ReactNode;
  id: string;
}

export const DropdownMenu = ({ children, id }: DropdownMenuProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 hover:bg-neutral-100 rounded"
      >
        <MoreHorizontal className="h-4 w-4" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-1 w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-50">
          <div className="py-1">{children}</div>
        </div>
      )}
    </div>
  );
};

export const DropdownMenuItem = ({
  children,
}: {
  children: React.ReactNode;
}) => <div className="px-4 py-2 hover:bg-neutral-100">{children}</div>;

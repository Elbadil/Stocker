import { Modal, Fade } from '@mui/material';
import { ReactNode } from 'react';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
}

const ModalOverlay = ({ isOpen, onClose, children }: ModalProps) => {
  return (
    <Modal
      open={isOpen}
      onClose={onClose}
      disableScrollLock={true}
      closeAfterTransition={true}
      disablePortal={false}
      container={document.body}
      keepMounted={true}
      className={`fixed inset-0 z-[50]`}
    >
      <Fade in={isOpen} timeout={500}>
        <div className="relative h-full w-full">
          {/* Full screen overlay */}
          <div
            className="absolute inset-0 bg-black bg-opacity-40"
            onClick={onClose}
          />

          {/* Modal content */}
          <div
            onClick={(e) => e.stopPropagation()}
            className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-full max-w-md rounded-lg"
          >
            {children}
          </div>
        </div>
      </Fade>
    </Modal>
  );
};

export default ModalOverlay;

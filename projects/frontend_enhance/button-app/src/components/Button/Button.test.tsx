import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Button from './';
import { describe, it, expect, vi } from 'vitest';
import CustomComp from './__test-utils__/CustomComp';

describe('Button (Polymorphic)', () => {
  it('renders as a default button and handles click', () => {
    const onClick = vi.fn();
    render(
      <Button onClick={onClick} ariaLabel="Submit">
        Submit
      </Button>
    );
    const btn = screen.getByRole('button', { name: 'Submit' });
    expect(btn).toBeInTheDocument();
    fireEvent.click(btn);
    expect(onClick).toHaveBeenCalled();
  });

  it('renders as a polymorphic anchor when as="a"', () => {
    const onClick = vi.fn();
    render(
      <Button as="a" href="/path" onClick={onClick} ariaLabel="Go">
        Go
      </Button>
    );
    const anchor = screen.getByRole('button', { name: 'Go' });
    expect(anchor.tagName).toBe('A');
    fireEvent.click(anchor);
    expect(onClick).toHaveBeenCalled();
  });

  it('loading state shows a spinner with aria-label and blocks onClick', () => {
    const onClick = vi.fn();
    render(
      <Button onClick={onClick} ariaLabel="Submit" loading>
        Submit
      </Button>
    );
    const btn = screen.getByRole('button', { name: 'Submit' });
    const spinner = screen.getByLabelText('Loading');
    expect(spinner).toBeInTheDocument();
    expect(btn).toBeInTheDocument();
    fireEvent.click(btn);
    expect(onClick).not.toHaveBeenCalled();
  });

  it('non-button As is accessible via keyboard (Enter/Space) and triggers onClick', () => {
    const onClick = vi.fn();
    render(
      <Button as="a" href="/path" onClick={onClick} ariaLabel="Action">
        Action
      </Button>
    );
    const el = screen.getByRole('button', { name: 'Action' });
    // Simulate Enter
    fireEvent.keyDown(el, { key: 'Enter', code: 'Enter' });
    expect(onClick).toHaveBeenCalled();
  });

  it('ref forwards to the underlying element (button, a, custom)', () => {
    // Button default
    const ref1 = React.createRef<HTMLButtonElement>();
    render(
      <Button ref={ref1} ariaLabel="Button">
        Text
      </Button>
    );
    // @ts-ignore
    expect(ref1.current.tagName).toBe('BUTTON');

    // Anchor
    const ref2 = React.createRef<HTMLAnchorElement>();
    render(
      <Button as="a" href="#" ref={ref2} ariaLabel="Link">
        Home
      </Button>
    );
    // @ts-ignore
    expect(ref2.current.tagName).toBe('A');

    // Custom component
    const Custom = React.forwardRef<HTMLDivElement, any>((props, ref) => (
      <div ref={ref} {...props} data-testid="custom-root" />
    ));
    const ref3 = React.createRef<HTMLDivElement>();
    render(
      <Button as={Custom} ref={ref3} ariaLabel="Custom">
        C
      </Button>
    );
    // @ts-ignore
    expect(ref3.current.tagName).toBe('DIV');
  });
});